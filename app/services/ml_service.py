"""
Serviço de Machine Learning
Responsável por análise estatística e detecção de anomalias
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
from scipy import stats
import joblib
import os

from app.services.database_service import DatabaseService
from app.utils.logger import setup_logger

# Configurar logger
logger = setup_logger(__name__)

class MLService:
    """Serviço de Machine Learning para análise de dados NTP"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models')
        
        # Criar diretório de modelos se não existir
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Configurações dos modelos
        self.isolation_forest = None
        self.scaler = StandardScaler()
        self.dbscan = None
        
        # Parâmetros de configuração
        self.anomaly_threshold = 0.05  # 5% de anomalias esperadas
        self.min_samples_for_training = 100
        self.model_update_interval = timedelta(hours=24)
        
        # Cache de modelos
        self._models_cache = {}
        self._last_training = {}
    
    async def detect_anomalies(
        self,
        server_id: int,
        lookback_hours: int = 24,
        method: str = 'isolation_forest'
    ) -> Dict[str, Any]:
        """
        Detectar anomalias nos dados de um servidor
        
        Args:
            server_id: ID do servidor
            lookback_hours: Horas para análise retrospectiva
            method: Método de detecção ('isolation_forest', 'statistical', 'clustering')
            
        Returns:
            Dicionário com resultados da detecção
        """
        try:
            logger.info(f"Detectando anomalias para servidor {server_id} usando método {method}")
            
            # Obter dados históricos
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=lookback_hours)
            
            data = self.db_service.get_server_metrics_history(server_id, start_time, end_time)
            
            if len(data) < self.min_samples_for_training:
                return {
                    'anomalies_detected': False,
                    'reason': 'Dados insuficientes para análise',
                    'sample_count': len(data)
                }
            
            # Preparar dados
            df = pd.DataFrame(data)
            features = self._prepare_features(df)
            
            # Detectar anomalias baseado no método
            if method == 'isolation_forest':
                results = await self._detect_with_isolation_forest(server_id, features, df)
            elif method == 'statistical':
                results = await self._detect_with_statistical_methods(features, df)
            elif method == 'clustering':
                results = await self._detect_with_clustering(features, df)
            else:
                raise ValueError(f"Método não suportado: {method}")
            
            # Adicionar contexto temporal
            results['analysis_period'] = {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'hours': lookback_hours
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Erro na detecção de anomalias: {e}")
            raise
    
    def _prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """Preparar features para análise de ML"""
        features = []
        
        # Features básicas
        if 'response_time' in df.columns:
            features.append(df['response_time'].values)
        if 'offset' in df.columns:
            features.append(df['offset'].values)
        if 'delay' in df.columns:
            features.append(df['delay'].values)
        if 'dispersion' in df.columns:
            features.append(df['dispersion'].values)
        
        # Features derivadas
        if 'response_time' in df.columns:
            # Média móvel do tempo de resposta
            features.append(df['response_time'].rolling(window=5, min_periods=1).mean().values)
            # Desvio padrão móvel
            features.append(df['response_time'].rolling(window=5, min_periods=1).std().fillna(0).values)
        
        if 'offset' in df.columns:
            # Taxa de mudança do offset
            features.append(df['offset'].diff().fillna(0).values)
            # Offset absoluto
            features.append(np.abs(df['offset']).values)
        
        # Converter para array numpy
        features_array = np.column_stack(features)
        
        # Remover NaN e infinitos
        features_array = np.nan_to_num(features_array, nan=0.0, posinf=0.0, neginf=0.0)
        
        return features_array
    
    async def _detect_with_isolation_forest(
        self,
        server_id: int,
        features: np.ndarray,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Detectar anomalias usando Isolation Forest"""
        
        # Verificar se precisa treinar/atualizar modelo
        model_key = f"isolation_forest_{server_id}"
        
        if (model_key not in self._models_cache or 
            self._should_retrain_model(server_id)):
            
            logger.info(f"Treinando modelo Isolation Forest para servidor {server_id}")
            
            # Treinar novo modelo
            model = IsolationForest(
                contamination=self.anomaly_threshold,
                random_state=42,
                n_estimators=100
            )
            
            # Normalizar features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Treinar modelo
            model.fit(features_scaled)
            
            # Salvar modelo e scaler
            self._models_cache[model_key] = {
                'model': model,
                'scaler': scaler,
                'trained_at': datetime.now()
            }
            
            self._last_training[server_id] = datetime.now()
            
            # Salvar modelo em disco
            model_path = os.path.join(self.models_dir, f'isolation_forest_{server_id}.joblib')
            scaler_path = os.path.join(self.models_dir, f'scaler_{server_id}.joblib')
            
            joblib.dump(model, model_path)
            joblib.dump(scaler, scaler_path)
        
        else:
            # Usar modelo existente
            model = self._models_cache[model_key]['model']
            scaler = self._models_cache[model_key]['scaler']
        
        # Normalizar features
        features_scaled = scaler.transform(features)
        
        # Detectar anomalias
        anomaly_labels = model.predict(features_scaled)
        anomaly_scores = model.decision_function(features_scaled)
        
        # Processar resultados
        anomalies_mask = anomaly_labels == -1
        anomaly_indices = np.where(anomalies_mask)[0]
        
        anomalies = []
        for idx in anomaly_indices:
            anomaly_data = {
                'timestamp': df.iloc[idx]['timestamp'].isoformat() if 'timestamp' in df.columns else None,
                'index': int(idx),
                'score': float(anomaly_scores[idx]),
                'metrics': {}
            }
            
            # Adicionar métricas da anomalia
            for col in ['response_time', 'offset', 'delay', 'dispersion']:
                if col in df.columns:
                    anomaly_data['metrics'][col] = float(df.iloc[idx][col])
            
            anomalies.append(anomaly_data)
        
        return {
            'anomalies_detected': len(anomalies) > 0,
            'method': 'isolation_forest',
            'total_samples': len(features),
            'anomaly_count': len(anomalies),
            'anomaly_rate': len(anomalies) / len(features),
            'anomalies': anomalies,
            'model_info': {
                'trained_at': self._models_cache[model_key]['trained_at'].isoformat(),
                'contamination': self.anomaly_threshold
            }
        }
    
    async def _detect_with_statistical_methods(
        self,
        features: np.ndarray,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Detectar anomalias usando métodos estatísticos"""
        
        anomalies = []
        
        # Z-score para cada feature
        for i, col in enumerate(['response_time', 'offset', 'delay', 'dispersion']):
            if i >= features.shape[1] or col not in df.columns:
                continue
                
            feature_data = features[:, i]
            z_scores = np.abs(stats.zscore(feature_data))
            
            # Anomalias com Z-score > 3
            anomaly_indices = np.where(z_scores > 3)[0]
            
            for idx in anomaly_indices:
                anomaly_data = {
                    'timestamp': df.iloc[idx]['timestamp'].isoformat() if 'timestamp' in df.columns else None,
                    'index': int(idx),
                    'feature': col,
                    'z_score': float(z_scores[idx]),
                    'value': float(feature_data[idx]),
                    'method': 'z_score'
                }
                anomalies.append(anomaly_data)
        
        # IQR (Interquartile Range) method
        for i, col in enumerate(['response_time', 'offset', 'delay', 'dispersion']):
            if i >= features.shape[1] or col not in df.columns:
                continue
                
            feature_data = features[:, i]
            Q1 = np.percentile(feature_data, 25)
            Q3 = np.percentile(feature_data, 75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            anomaly_indices = np.where(
                (feature_data < lower_bound) | (feature_data > upper_bound)
            )[0]
            
            for idx in anomaly_indices:
                anomaly_data = {
                    'timestamp': df.iloc[idx]['timestamp'].isoformat() if 'timestamp' in df.columns else None,
                    'index': int(idx),
                    'feature': col,
                    'value': float(feature_data[idx]),
                    'lower_bound': float(lower_bound),
                    'upper_bound': float(upper_bound),
                    'method': 'iqr'
                }
                anomalies.append(anomaly_data)
        
        # Remover duplicatas baseado no índice
        unique_anomalies = {}
        for anomaly in anomalies:
            idx = anomaly['index']
            if idx not in unique_anomalies:
                unique_anomalies[idx] = anomaly
        
        final_anomalies = list(unique_anomalies.values())
        
        return {
            'anomalies_detected': len(final_anomalies) > 0,
            'method': 'statistical',
            'total_samples': len(features),
            'anomaly_count': len(final_anomalies),
            'anomaly_rate': len(final_anomalies) / len(features),
            'anomalies': final_anomalies
        }
    
    async def _detect_with_clustering(
        self,
        features: np.ndarray,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Detectar anomalias usando clustering (DBSCAN)"""
        
        # Normalizar features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # Aplicar DBSCAN
        dbscan = DBSCAN(eps=0.5, min_samples=5)
        cluster_labels = dbscan.fit_predict(features_scaled)
        
        # Pontos com label -1 são considerados outliers/anomalias
        anomaly_indices = np.where(cluster_labels == -1)[0]
        
        anomalies = []
        for idx in anomaly_indices:
            anomaly_data = {
                'timestamp': df.iloc[idx]['timestamp'].isoformat() if 'timestamp' in df.columns else None,
                'index': int(idx),
                'cluster_label': int(cluster_labels[idx]),
                'metrics': {}
            }
            
            # Adicionar métricas da anomalia
            for col in ['response_time', 'offset', 'delay', 'dispersion']:
                if col in df.columns:
                    anomaly_data['metrics'][col] = float(df.iloc[idx][col])
            
            anomalies.append(anomaly_data)
        
        # Estatísticas dos clusters
        unique_clusters = np.unique(cluster_labels[cluster_labels != -1])
        cluster_stats = {
            'total_clusters': len(unique_clusters),
            'cluster_sizes': {}
        }
        
        for cluster_id in unique_clusters:
            cluster_size = np.sum(cluster_labels == cluster_id)
            cluster_stats['cluster_sizes'][str(cluster_id)] = int(cluster_size)
        
        return {
            'anomalies_detected': len(anomalies) > 0,
            'method': 'clustering',
            'total_samples': len(features),
            'anomaly_count': len(anomalies),
            'anomaly_rate': len(anomalies) / len(features),
            'anomalies': anomalies,
            'cluster_info': cluster_stats
        }
    
    def _should_retrain_model(self, server_id: int) -> bool:
        """Verificar se o modelo deve ser retreinado"""
        if server_id not in self._last_training:
            return True
        
        last_training = self._last_training[server_id]
        return datetime.now() - last_training > self.model_update_interval
    
    async def analyze_trends(
        self,
        server_id: int,
        lookback_days: int = 7
    ) -> Dict[str, Any]:
        """
        Analisar tendências nos dados do servidor
        
        Args:
            server_id: ID do servidor
            lookback_days: Dias para análise retrospectiva
            
        Returns:
            Análise de tendências
        """
        try:
            logger.info(f"Analisando tendências para servidor {server_id}")
            
            # Obter dados históricos
            end_time = datetime.now()
            start_time = end_time - timedelta(days=lookback_days)
            
            data = self.db_service.get_server_metrics_history(server_id, start_time, end_time)
            
            if len(data) < 10:
                return {
                    'trends_available': False,
                    'reason': 'Dados insuficientes para análise de tendências'
                }
            
            df = pd.DataFrame(data)
            
            # Análise de tendências para cada métrica
            trends = {}
            
            for metric in ['response_time', 'offset', 'delay', 'dispersion']:
                if metric in df.columns:
                    values = df[metric].values
                    
                    # Regressão linear simples para tendência
                    x = np.arange(len(values))
                    slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
                    
                    # Classificar tendência
                    if abs(slope) < std_err:
                        trend_direction = 'stable'
                    elif slope > 0:
                        trend_direction = 'increasing'
                    else:
                        trend_direction = 'decreasing'
                    
                    trends[metric] = {
                        'direction': trend_direction,
                        'slope': float(slope),
                        'r_squared': float(r_value ** 2),
                        'p_value': float(p_value),
                        'confidence': 'high' if abs(r_value) > 0.7 else 'medium' if abs(r_value) > 0.3 else 'low'
                    }
            
            return {
                'trends_available': True,
                'analysis_period': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'days': lookback_days
                },
                'trends': trends,
                'sample_count': len(data)
            }
            
        except Exception as e:
            logger.error(f"Erro na análise de tendências: {e}")
            raise
    
    async def predict_future_values(
        self,
        server_id: int,
        metric: str,
        hours_ahead: int = 24
    ) -> Dict[str, Any]:
        """
        Prever valores futuros de uma métrica
        
        Args:
            server_id: ID do servidor
            metric: Métrica a prever ('response_time', 'offset', etc.)
            hours_ahead: Horas para previsão
            
        Returns:
            Previsões futuras
        """
        try:
            logger.info(f"Prevendo valores futuros de {metric} para servidor {server_id}")
            
            # Obter dados históricos (últimos 7 dias)
            end_time = datetime.now()
            start_time = end_time - timedelta(days=7)
            
            data = self.db_service.get_server_metrics_history(server_id, start_time, end_time)
            
            if len(data) < 50:
                return {
                    'prediction_available': False,
                    'reason': 'Dados insuficientes para previsão'
                }
            
            df = pd.DataFrame(data)
            
            if metric not in df.columns:
                return {
                    'prediction_available': False,
                    'reason': f'Métrica {metric} não encontrada nos dados'
                }
            
            values = df[metric].values
            
            # Modelo simples de média móvel exponencial
            alpha = 0.3  # Fator de suavização
            predictions = []
            
            # Calcular média móvel exponencial
            ema = values[0]
            for value in values[1:]:
                ema = alpha * value + (1 - alpha) * ema
            
            # Gerar previsões
            current_prediction = ema
            for i in range(hours_ahead):
                predictions.append({
                    'hour': i + 1,
                    'predicted_value': float(current_prediction),
                    'timestamp': (end_time + timedelta(hours=i + 1)).isoformat()
                })
                
                # Adicionar pequena variação baseada no desvio padrão histórico
                std_dev = np.std(values[-24:]) if len(values) >= 24 else np.std(values)
                noise = np.random.normal(0, std_dev * 0.1)
                current_prediction += noise
            
            # Calcular intervalos de confiança
            recent_std = np.std(values[-24:]) if len(values) >= 24 else np.std(values)
            
            for pred in predictions:
                pred['confidence_interval'] = {
                    'lower': pred['predicted_value'] - 1.96 * recent_std,
                    'upper': pred['predicted_value'] + 1.96 * recent_std
                }
            
            return {
                'prediction_available': True,
                'metric': metric,
                'hours_ahead': hours_ahead,
                'predictions': predictions,
                'model_info': {
                    'type': 'exponential_moving_average',
                    'alpha': alpha,
                    'historical_samples': len(values)
                }
            }
            
        except Exception as e:
            logger.error(f"Erro na previsão de valores: {e}")
            raise