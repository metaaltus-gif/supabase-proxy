#!/usr/bin/env python3
"""
SUPABASE PROXY API
Deploy em Railway, Render ou qualquer servidor Python

Este proxy permite executar SQL no Supabase de qualquer lugar!
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import os
from functools import wraps

app = Flask(__name__)
CORS(app)

# Configuração via variáveis de ambiente
DATABASE_URL = os.getenv('DATABASE_URL')
API_KEY = os.getenv('API_KEY', 'sua-chave-secreta-aqui')

def require_api_key(f):
    """Decorator para proteger endpoints com API Key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        key = request.headers.get('X-API-Key')
        if key != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return jsonify({
        'service': 'Supabase Proxy API',
        'status': 'running',
        'version': '1.0',
        'endpoints': {
            '/execute': 'POST - Execute SQL',
            '/query': 'POST - Execute SELECT query',
            '/health': 'GET - Health check'
        }
    })

@app.route('/health')
def health():
    """Health check para Railway/Render"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/execute', methods=['POST'])
@require_api_key
def execute_sql():
    """
    Executa SQL (CREATE, INSERT, UPDATE, DELETE)
    
    Body:
    {
        "sql": "CREATE TABLE..."
    }
    """
    try:
        data = request.get_json()
        sql = data.get('sql')
        
        if not sql:
            return jsonify({'error': 'SQL is required'}), 400
        
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        cursor = conn.cursor()
        
        # Executar SQL
        cursor.execute(sql)
        conn.commit()
        
        # Pegar mensagens (se houver)
        messages = []
        if cursor.statusmessage:
            messages.append(cursor.statusmessage)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'messages': messages,
            'rows_affected': cursor.rowcount
        })
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({
            'status': 'error',
            'error': str(e),
            'type': type(e).__name__
        }), 400

@app.route('/query', methods=['POST'])
@require_api_key
def query_sql():
    """
    Executa SELECT query e retorna resultados
    
    Body:
    {
        "sql": "SELECT * FROM...",
        "params": [] (opcional)
    }
    """
    try:
        data = request.get_json()
        sql = data.get('sql')
        params = data.get('params', None)
        
        if not sql:
            return jsonify({'error': 'SQL is required'}), 400
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Executar query
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        
        # Pegar resultados
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        
        # Converter para dicionários
        results = []
        for row in rows:
            results.append(dict(zip(columns, row)))
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'data': results,
            'count': len(results)
        })
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({
            'status': 'error',
            'error': str(e),
            'type': type(e).__name__
        }), 400

@app.route('/batch', methods=['POST'])
@require_api_key
def batch_execute():
    """
    Executa múltiplos SQLs em transação
    
    Body:
    {
        "sqls": ["SQL1", "SQL2", ...]
    }
    """
    try:
        data = request.get_json()
        sqls = data.get('sqls', [])
        
        if not sqls:
            return jsonify({'error': 'sqls array is required'}), 400
        
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        cursor = conn.cursor()
        
        results = []
        
        for sql in sqls:
            cursor.execute(sql)
            results.append({
                'status': 'success',
                'rows_affected': cursor.rowcount
            })
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'results': results,
            'total': len(sqls)
        })
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({
            'status': 'error',
            'error': str(e),
            'type': type(e).__name__
        }), 400

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
