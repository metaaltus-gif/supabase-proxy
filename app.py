from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from urllib.parse import urlparse, urlunparse
import socket

app = Flask(__name__)

# Configuração
API_KEY = os.environ.get('API_KEY', 'change-me')
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_ipv4_connection_string(url):
    """Converte hostname para IPv4 para evitar problemas de IPv6"""
    parsed = urlparse(url)
    hostname = parsed.hostname
    
    try:
        # Resolver hostname para IPv4
        ipv4 = socket.getaddrinfo(hostname, None, socket.AF_INET)[0][4][0]
        # Substituir hostname por IP
        netloc = parsed.netloc.replace(hostname, ipv4)
        new_parsed = parsed._replace(netloc=netloc)
        return urlunparse(new_parsed)
    except:
        return url

def get_db_connection():
    """Cria conexão com banco usando IPv4"""
    conn_string = get_ipv4_connection_string(DATABASE_URL)
    return psycopg2.connect(conn_string)

def verify_api_key():
    """Verifica API Key"""
    key = request.headers.get('X-API-Key')
    if key != API_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
    return None

@app.route('/')
def index():
    return jsonify({
        'name': 'Supabase Proxy API',
        'version': '1.0',
        'endpoints': ['/health', '/execute', '/query', '/batch']
    })

@app.route('/health')
def health():
    """Health check com teste de conexão"""
    auth_error = verify_api_key()
    if auth_error:
        return auth_error
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'version': version[:50]
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/execute', methods=['POST'])
def execute_sql():
    """Executa SQL (CREATE, INSERT, UPDATE, DELETE)"""
    auth_error = verify_api_key()
    if auth_error:
        return auth_error
    
    data = request.get_json()
    sql = data.get('sql')
    
    if not sql:
        return jsonify({'error': 'SQL query required'}), 400
    
    try:
        conn = get_db_connection()
        conn.autocommit = False
        cursor = conn.cursor()
        
        cursor.execute(sql)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'SQL executed successfully'
        })
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/query', methods=['POST'])
def query_sql():
    """Executa SELECT e retorna resultados"""
    auth_error = verify_api_key()
    if auth_error:
        return auth_error
    
    data = request.get_json()
    sql = data.get('sql')
    
    if not sql:
        return jsonify({'error': 'SQL query required'}), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(sql)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'data': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/batch', methods=['POST'])
def batch_sql():
    """Executa múltiplos SQLs em transação"""
    auth_error = verify_api_key()
    if auth_error:
        return auth_error
    
    data = request.get_json()
    sqls = data.get('sqls', [])
    
    if not sqls:
        return jsonify({'error': 'SQL queries required'}), 400
    
    try:
        conn = get_db_connection()
        conn.autocommit = False
        cursor = conn.cursor()
        
        for sql in sqls:
            cursor.execute(sql)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': f'{len(sqls)} queries executed successfully'
        })
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
