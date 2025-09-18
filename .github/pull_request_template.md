# 🔄 Pull Request

## 📋 Descrição

Descreva brevemente as mudanças implementadas neste PR.

## 🎯 Tipo de Mudança

- [ ] 🐛 Bug fix (mudança que corrige um problema)
- [ ] ✨ Nova funcionalidade (mudança que adiciona funcionalidade)
- [ ] 💥 Breaking change (correção ou funcionalidade que causaria quebra de compatibilidade)
- [ ] 📚 Documentação (mudanças apenas na documentação)
- [ ] 🎨 Estilo (formatação, ponto e vírgula ausente, etc; sem mudança de código)
- [ ] ♻️ Refatoração (mudança de código que não corrige bug nem adiciona funcionalidade)
- [ ] ⚡ Performance (mudança que melhora performance)
- [ ] ✅ Testes (adição ou correção de testes)
- [ ] 🔧 Chore (mudanças no processo de build, ferramentas auxiliares, etc)

## 🔗 Issues Relacionadas

Fixes #(número da issue)
Closes #(número da issue)
Relates to #(número da issue)

## 🧪 Como Foi Testado?

Descreva os testes que você executou para verificar suas mudanças.

- [ ] Teste de conectividade (`python test_connectivity.py`)
- [ ] Teste de status (`python main.py --status`)
- [ ] Teste de sincronização única (`python main.py --once`)
- [ ] Teste de instalação do serviço
- [ ] Testes manuais específicos

**Configuração de Teste:**
- OS: [ex: Windows 10]
- Python: [ex: 3.9.0]
- Servidor NTP: [ex: pool.ntp.org]

## 📸 Screenshots (se aplicável)

Adicione screenshots para demonstrar as mudanças visuais.

## ✅ Checklist

### Código
- [ ] Meu código segue as diretrizes de estilo do projeto
- [ ] Realizei uma auto-revisão do meu código
- [ ] Comentei meu código, especialmente em áreas difíceis de entender
- [ ] Minhas mudanças não geram novos warnings
- [ ] Adicionei testes que provam que minha correção é efetiva ou que minha funcionalidade funciona

### Documentação
- [ ] Fiz mudanças correspondentes na documentação
- [ ] Atualizei o README.md se necessário
- [ ] Atualizei o CHANGELOG.md
- [ ] Atualizei o .env.example se necessário

### Testes
- [ ] Novos e existentes testes unitários passam localmente com minhas mudanças
- [ ] Testei em ambiente Windows
- [ ] Testei com privilégios administrativos
- [ ] Testei sem privilégios administrativos

### Segurança
- [ ] Não expus credenciais ou informações sensíveis
- [ ] Segui princípios de menor privilégio
- [ ] Validei todas as entradas de usuário
- [ ] Considerei implicações de segurança das mudanças

## 📝 Notas Adicionais

Adicione qualquer informação adicional que os revisores devem saber.

## 🔍 Revisão

- [ ] Este PR está pronto para revisão
- [ ] Este PR é um work in progress (WIP)

---

**Para os Revisores:**
- Verifiquem se o código segue os padrões do projeto
- Testem as funcionalidades em ambiente Windows
- Validem a documentação atualizada
- Confirmem que não há vazamentos de segurança