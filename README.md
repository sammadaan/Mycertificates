# 🏛️ Assistente de Correção Jurídica

Um sistema completo de correção gramatical e de coesão para textos jurídicos brasileiros, com coleta automatizada de dados e aprendizado contínuo.

## 📋 Funcionalidades Principais

### 🎯 Correção de Textos
- ✅ **Interface web moderna** - Chat interface responsiva e intuitiva
- ✅ **Correção automática** - Gramática e coesão usando IA (Gemini API)
- ✅ **Foco jurídico** - Especializado em linguagem legal brasileira
- ✅ **Comparação lado a lado** - Mostra texto original e corrigido
- ✅ **Correção contextual** - Usa base de dados para melhorar a qualidade

### 🕷️ Coleta Automatizada de Dados
- ✅ **Web Scraping** - Coleta automática de STF, STJ, ConJur e Migalhas
- ✅ **Agendamento semanal** - Execução automática todos os segundas às 02:00
- ✅ **Processamento inteligente** - Limpeza e categorização automática
- ✅ **Banco de dados** - SQLite com indexação e controle de qualidade
- ✅ **Monitoramento** - Logs, alertas e estatísticas em tempo real

### 🔧 Painel Administrativo
- ✅ **Dashboard completo** - Monitoramento em tempo real
- ✅ **Controle manual** - Execução sob demanda de coletas
- ✅ **Pesquisa avançada** - Busca na base de dados coletados
- ✅ **Manutenção** - Limpeza e backup automático
- ✅ **Geração de dados** - Exportação para treinamento de modelos

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
├── app.py                      # Backend Flask principal com API completa
├── database.py                 # Sistema de banco de dados SQLite
├── legal_scrapers.py          # Web scrapers para fontes jurídicas
├── data_processor.py          # Pipeline de processamento e limpeza
├── scheduler.py               # Sistema de agendamento automático
├── setup_colab.py             # Script de configuração para Google Colab
├── requirements.txt           # Dependências Python
├── templates/
│   ├── index.html            # Interface de correção de textos
│   └── admin_dashboard.html  # Painel administrativo
├── Legal_Text_Corrector_Demo.ipynb  # Notebook para Google Colab
└── README.md                 # Este arquivo
```

## 🔧 Tecnologias Utilizadas

### Backend
- **Flask** - Framework web Python
- **SQLite** - Banco de dados embedado
- **BeautifulSoup4** - Parser HTML/XML para web scraping
- **Requests** - Cliente HTTP para coleta de dados
- **Schedule** - Agendamento de tarefas automáticas

### Frontend
- **HTML5, CSS3, JavaScript** - Interface web responsiva
- **CSS Grid & Flexbox** - Layout moderno
- **Fetch API** - Comunicação assíncrona com backend

### IA e Processamento
- **Google Gemini API** - Modelo de linguagem para correções
- **Regex** - Processamento e extração de entidades legais
- **NLP** - Análise e categorização de textos jurídicos

### Infraestrutura
- **ngrok** - Túnel para acesso público (Colab)
- **Threading** - Processamento paralelo
- **Logging** - Sistema de logs estruturado

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

## 🚀 Funcionalidades Avançadas

### Sistema de Coleta Automatizada
O sistema inclui web scrapers para as seguintes fontes:
- **STF** - Supremo Tribunal Federal (decisões e acórdãos)
- **STJ** - Superior Tribunal de Justiça (jurisprudência)
- **ConJur** - Consultor Jurídico (notícias e análises)
- **Migalhas** - Portal jurídico (artigos e notícias)

### Processamento Inteligente
- **Limpeza automática** - Remove artefatos e normaliza formatação
- **Extração de entidades** - Identifica leis, artigos, processos
- **Categorização** - Classifica por área do direito
- **Análise de qualidade** - Score baseado em múltiplos fatores
- **Enriquecimento com IA** - Análise contextual usando Gemini

### Agendamento e Monitoramento
- **Execução semanal** - Automática toda segunda-feira às 02:00
- **Logs estruturados** - Rastreamento de todas as operações
- **Alertas por email** - Notificações de problemas ou sucessos
- **Dashboard em tempo real** - Estatísticas e controles administrativos
- **Backup automático** - Proteção dos dados coletados

## 🔧 Deployment em Produção

### Usando Docker (Recomendado)
```bash
# Clone o repositório
git clone <repo-url>
cd legal-text-corrector

# Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com suas configurações

# Build e execute
docker-compose up -d
```

### Instalação Manual
```bash
# Instale as dependências
pip install -r requirements.txt

# Configure a API key
export GEMINI_API_KEY="sua-chave-aqui"

# Execute o servidor
python app.py

# Em outro terminal, inicie o agendador
python scheduler.py --start
```

### Acessos
- **Interface Principal:** http://localhost:5000
- **Dashboard Admin:** http://localhost:5000/api/admin/dashboard
- **API Health Check:** http://localhost:5000/api/health

## 📊 Endpoints da API

### Correção de Textos
- `POST /api/correct` - Correção básica
- `POST /api/correct/enhanced` - Correção com contexto do banco de dados

### Administração
- `GET /api/admin/stats` - Estatísticas gerais
- `POST /api/admin/scrape/manual` - Executar coleta manual
- `POST /api/admin/process/texts` - Processar textos pendentes
- `GET /api/admin/database/search` - Pesquisar na base de dados

### Agendador
- `POST /api/admin/scheduler/start` - Iniciar agendador
- `POST /api/admin/scheduler/stop` - Parar agendador

## 📜 Licença

Este projeto foi desenvolvido como protótipo para advogados brasileiros. Uso livre para fins educacionais e profissionais.