# 🤝 Guia de Contribuição

Obrigado por considerar contribuir para o Sistema de Sincronização Automática de Hora! Este documento fornece diretrizes para contribuir com o projeto.

## 📋 Código de Conduta

Este projeto adere a um código de conduta. Ao participar, você deve manter um ambiente respeitoso e inclusivo.

## 🚀 Como Contribuir

### 1. Reportando Bugs

Antes de reportar um bug:
- Verifique se já existe uma issue similar
- Use a versão mais recente do projeto
- Teste em um ambiente limpo

**Template para Bug Report:**
```
**Descrição do Bug**
Descrição clara e concisa do problema.

**Passos para Reproduzir**
1. Vá para '...'
2. Clique em '....'
3. Execute '....'
4. Veja o erro

**Comportamento Esperado**
Descrição do que deveria acontecer.

**Screenshots/Logs**
Se aplicável, adicione screenshots ou logs.

**Ambiente:**
- OS: [ex: Windows 10]
- Python: [ex: 3.9.0]
- Versão do projeto: [ex: 1.0.0]
```

### 2. Sugerindo Melhorias

**Template para Feature Request:**
```
**Descrição da Funcionalidade**
Descrição clara da funcionalidade desejada.

**Problema que Resolve**
Explique o problema que esta funcionalidade resolveria.

**Solução Proposta**
Descrição detalhada de como implementar.

**Alternativas Consideradas**
Outras soluções que você considerou.
```

### 3. Contribuindo com Código

#### Configuração do Ambiente de Desenvolvimento

```bash
# 1. Fork o repositório
# 2. Clone seu fork
git clone https://github.com/seuusuario/projeto-automatic-windows-hora.git
cd projeto-automatic-windows-hora

# 3. Crie um ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows

# 4. Instale dependências
pip install -r requirements.txt

# 5. Crie uma branch para sua feature
git checkout -b feature/nova-funcionalidade
```

#### Padrões de Código

- **Estilo**: Siga PEP 8
- **Documentação**: Docstrings para todas as funções públicas
- **Comentários**: Código em inglês, comentários em português
- **Testes**: Adicione testes para novas funcionalidades

#### Estrutura de Commits

Use mensagens de commit descritivas:
```
tipo(escopo): descrição breve

Descrição mais detalhada se necessário.

- Mudança específica 1
- Mudança específica 2
```

**Tipos de commit:**
- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Documentação
- `style`: Formatação
- `refactor`: Refatoração
- `test`: Testes
- `chore`: Tarefas de manutenção

#### Processo de Pull Request

1. **Atualize sua branch** com a main mais recente
2. **Execute os testes** e certifique-se que passam
3. **Atualize a documentação** se necessário
4. **Crie o Pull Request** com:
   - Título descritivo
   - Descrição detalhada das mudanças
   - Referência a issues relacionadas
   - Screenshots se aplicável

#### Checklist do Pull Request

- [ ] Código segue os padrões do projeto
- [ ] Testes foram adicionados/atualizados
- [ ] Documentação foi atualizada
- [ ] Commits seguem o padrão estabelecido
- [ ] Branch está atualizada com main
- [ ] Não há conflitos de merge

## 🧪 Executando Testes

```bash
# Teste de conectividade
python test_connectivity.py

# Teste de funcionalidades (como admin)
python main.py --status
```

## 📚 Documentação

- Mantenha o README.md atualizado
- Documente novas configurações no .env.example
- Adicione comentários em código complexo
- Atualize o CHANGELOG.md

## 🔒 Segurança

- **Nunca** commite credenciais ou chaves
- Use variáveis de ambiente para dados sensíveis
- Reporte vulnerabilidades de segurança privadamente
- Siga princípios de menor privilégio

## 📞 Dúvidas?

- Abra uma [Discussion](../../discussions)
- Crie uma [Issue](../../issues) com a tag `question`
- Consulte a documentação existente

## 🎉 Reconhecimento

Contribuidores serão reconhecidos no README.md e releases.

Obrigado por contribuir! 🚀