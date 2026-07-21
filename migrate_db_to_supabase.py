import sqlite3
import psycopg2
import psycopg2.extras
import os

# 1. ใส่ Connection String ของ Supabase ของคุณตรงนี้
SUPABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres")

def migrate():
    # เชื่อมต่อ SQLite (ฐานข้อมูลเดิม)
    sqlite_conn = sqlite3.connect('database.db')
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()
    
    # เชื่อมต่อ PostgreSQL (Supabase)
    try:
        pg_conn = psycopg2.connect(SUPABASE_URL)
        pg_cur = pg_conn.cursor()
        print("เชื่อมต่อ Supabase สำเร็จ!")
    except Exception as e:
        print(f"เชื่อมต่อ Supabase ไม่สำเร็จ: {e}")
        return

    # -- ตัวอย่างการย้ายตาราง users --
    print("เริ่มย้ายข้อมูลตาราง users...")
    
    # ดึงข้อมูลจาก SQLite
    sqlite_cur.execute("SELECT * FROM users")
    users = sqlite_cur.fetchall()
    
    for user in users:
        # เช็คว่ามีข้อมูลนี้ใน Supabase หรือยัง
        pg_cur.execute("SELECT id FROM users WHERE username = %s", (user['username'],))
        if not pg_cur.fetchone():
            # ถ้ายังไม่มี ให้ Insert
            try:
                pg_cur.execute('''
                    INSERT INTO users (username, email, password, role, score, rank)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    user['username'], 
                    user['email'], 
                    user['password'], 
                    user['role'] if 'role' in user.keys() else 'user',
                    user['score'] if 'score' in user.keys() else 0,
                    user['rank'] if 'rank' in user.keys() else 'หยาดน้ำทะเล'
                ))
                print(f"Migrated user: {user['username']}")
            except Exception as e:
                print(f"Error migrating {user['username']}: {e}")
                pg_conn.rollback()
        else:
            print(f"User {user['username']} already exists in Supabase, skipping.")
    
    pg_conn.commit()
    print("ย้ายตาราง users เสร็จสิ้น!")
    
    # คุณสามารถเพิ่มโค้ดสำหรับย้ายตารางอื่นๆ ได้แบบเดียวกันที่นี่...
    
    # ปิดการเชื่อมต่อ
    sqlite_conn.close()
    pg_conn.close()
    print("Migration Complete!")

if __name__ == "__main__":
    migrate()
