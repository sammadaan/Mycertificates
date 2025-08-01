# 🏛️ Assistente de Correção Jurídica

Um chatbot especializado em correção gramatical e de coesão para textos jurídicos brasileiros, mantendo o significado legal intacto.

## 📋 Funcionalidades

- ✅ **Interface web moderna** - Chat interface responsiva e intuitiva
- ✅ **Correção automática** - Gramática e coesão usando IA (Gemini API)
- ✅ **Foco jurídico** - Especializado em linguagem legal brasileira
- ✅ **Comparação lado a lado** - Mostra texto original e corrigido
- ✅ **Pronto para Google Colab** - Setup automático para ambiente Colab

## 🚀 Como Usar no Google Colab

### 1️⃣ Upload dos Arquivos
1. Faça upload dos seguintes arquivos para o Google Colab:
   - `app.py` (backend Flask)
   - `setup_colab.py` (script de configuração)
   - `templates/index.html` (frontend)

### 2️⃣ Configure sua API Key do Gemini
```python
# Execute em uma célula do Colab:
import os
os.environ['GEMINI_API_KEY'] = 'sua-chave-api-aqui'
```

**Como obter a API Key:**
1. Acesse [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crie uma nova API key
3. Copie e cole no código acima

### 3️⃣ Execute o Setup
```python
# Execute em uma célula do Colab:
exec(open('setup_colab.py').read())
```

### 4️⃣ Pronto! 
O script irá:
- 📦 Instalar todas as dependências
- 🔑 Verificar a configuração da API
- 🌐 Criar um túnel público com ngrok
- 🚀 Iniciar a aplicação Flask
- 📋 Exibir o link público para acesso

## 🧪 Exemplo de Teste

**Texto Original (Informal):**
```
O cara simplesmente não fez o que prometeu no papel que a gente assinou, e agora estou perdendo dinheiro e me sentindo super estressado com isso. Tentei conversar com ele várias vezes, mas ele não responde, e agora acho que o tribunal precisa resolver isso porque não é justo.
```

**Texto Corrigido (Formal Jurídico):**
```
O Requerido deixou de cumprir as obrigações estabelecidas no instrumento contratual firmado entre as partes, resultando em prejuízos financeiros e danos morais ao Requerente. Apesar de diversas tentativas de composição amigável, o Requerido manteve-se inerte, tornando necessária a intervenção do Poder Judiciário para garantir o cumprimento das obrigações contratuais e a devida reparação dos danos causados.
```

## 📁 Estrutura do Projeto

```
legal-text-corrector/
├── app.py                 # Backend Flask com integração Gemini API
├── setup_colab.py         # Script de configuração para Google Colab
├── requirements.txt       # Dependências Python
├── templates/
│   └── index.html        # Frontend (HTML + CSS + JavaScript)
└── README.md             # Este arquivo
```

## 🔧 Tecnologias Utilizadas

- **Backend:** Flask (Python)
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **IA:** Google Gemini API
- **Túnel:** ngrok (para acesso público no Colab)
- **Estilo:** CSS moderno com gradientes e animações

## 🎯 Características Técnicas

### Backend (Flask)
- Endpoint `/api/correct` para correção de texto
- Integração com Gemini API
- Tratamento de erros robusto
- CORS habilitado para desenvolvimento
- Logging configurado

### Frontend
- Interface responsiva (mobile-friendly)
- Loading states e feedback visual
- Auto-resize da textarea
- Shortcuts de teclado (Ctrl+Enter)
- Tratamento de erros
- Exemplo pré-carregado

### Prompt Especializado
- Foco em textos jurídicos brasileiros
- Preservação do significado legal
- Melhoria apenas de gramática e coesão
- Transformação de linguagem informal para formal jurídica

## 🔐 Segurança

- API key armazenada como variável de ambiente
- Validação de entrada no backend
- Tratamento seguro de erros
- CORS configurado adequadamente

## 🚨 Limitações

- Requer API key válida do Google Gemini
- Túnel ngrok tem limitações na versão gratuita
- Dependente de conexão com internet
- Tempo de resposta varia conforme API

## 📞 Suporte

Para problemas ou dúvidas:
1. Verifique se a API key está configurada corretamente
2. Certifique-se de que todos os arquivos foram uploadados
3. Execute `quick_test()` para verificar a conectividade
4. Consulte os logs no console do Colab

## 📜 Licença

Este projeto foi desenvolvido como protótipo para advogados brasileiros. Uso livre para fins educacionais e profissionais.