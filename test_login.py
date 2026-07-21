import os
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash

SUPABASE_URL = "postgresql://postgres:0800977581Thak.@db.byldkndfngdgcrazqyyx.supabase.co:5432/postgres"
os.environ["DATABASE_URL"] = SUPABASE_URL

class PostgresConnection:
    def __init__(self, conn):
        self.conn = conn
        
    def execute(self, query, params=None):
        query = query.replace('?', '%s')
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(query, params)
        return cur
        
    def commit(self):
        self.conn.commit()
        
    def close(self):
        self.conn.close()

def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    conn = psycopg2.connect(db_url)
    return PostgresConnection(conn)

try:
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users LIMIT 1 OFFSET 1').fetchone()
    conn.close()
    
    if user:
        print("User:", user['username'])
        if user['username'] == 'Thak' and user['email'] == 'skillrodchan@gmail.com':
            pass
        else:
            role = user['role'] if 'role' in user.keys() else 'user'
            print("Success, role:", role)
except Exception as e:
    import traceback
    traceback.print_exc()
