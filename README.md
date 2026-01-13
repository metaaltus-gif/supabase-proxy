# 🚀 Supabase Proxy API

Proxy API Flask para executar SQL no Supabase de qualquer lugar.

## 📦 Arquivos

- `app.py` - API Flask principal
- `requirements.txt` - Dependências Python
- `Procfile` - Configuração para Heroku/Railway
- `railway.json` - Configuração específica Railway
- `.env.example` - Exemplo de variáveis de ambiente
- `DEPLOY_RAILWAY.md` - Guia completo de deploy

## 🚀 Deploy Rápido

### Railway (Recomendado)
```bash
railway init
railway up
```

### Render
1. Conecte o repositório
2. Configure variáveis de ambiente
3. Deploy automático

### Heroku
```bash
heroku create
git push heroku main
```

## 🔧 Variáveis de Ambiente

```env
DATABASE_URL=postgresql://...
API_KEY=sua-chave-secreta
PORT=5000
```

## 📡 Endpoints

### GET /
Informações da API

### GET /health
Health check

### POST /execute
Executar SQL (CREATE, INSERT, UPDATE, DELETE)

Body:
```json
{
  "sql": "CREATE TABLE..."
}
```

Headers:
```
X-API-Key: sua-chave-secreta
```

### POST /query
Executar SELECT e retornar resultados

Body:
```json
{
  "sql": "SELECT * FROM...",
  "params": [] (opcional)
}
```

### POST /batch
Executar múltiplos SQLs em transação

Body:
```json
{
  "sqls": ["SQL1", "SQL2", ...]
}
```

## 🔐 Segurança

- ✅ API Key obrigatória
- ✅ CORS configurado
- ✅ SSL via Railway/Render
- ✅ Transações protegidas

## 💻 Desenvolvimento Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar .env
cp .env.example .env
# (edite o .env com suas credenciais)

# Rodar
python app.py
```

## 📊 Exemplo de Uso

```python
import requests

url = "https://seu-proxy.railway.app/execute"
headers = {"X-API-Key": "sua-chave"}
data = {"sql": "CREATE TABLE test (id serial)"}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

## 🎯 Após Deploy

Me envie:
1. URL do proxy
2. API Key

E nunca mais precisará executar SQL manualmente! 🎉
