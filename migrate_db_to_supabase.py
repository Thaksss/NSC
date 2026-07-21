import sqlite3
import psycopg2
import psycopg2.extras
import os
from datetime import datetime

# 1. ใส่ Connection String ของ Supabase ของคุณตรงนี้
SUPABASE_URL = os.environ.get("DATABASE_URL", "")

def migrate():
    if not SUPABASE_URL:
        print("Error: กรุณาตั้งค่า DATABASE_URL ใน Environment Variables ก่อนรัน")
        return

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

    # --- 1. ตาราง users ---
    print("เริ่มย้ายข้อมูลตาราง users...")
    sqlite_cur.execute("SELECT * FROM users")
    users = sqlite_cur.fetchall()
    
    for user in users:
        pg_cur.execute("SELECT id FROM users WHERE username = %s", (user['username'],))
        if not pg_cur.fetchone():
            try:
                pg_cur.execute('''
                    INSERT INTO users (username, email, password, role, score, rank)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    user['username'], user['email'], user['password'], 
                    user['role'] if 'role' in user.keys() else 'user',
                    user['score'] if 'score' in user.keys() else 0,
                    user['rank'] if 'rank' in user.keys() else 'หยาดน้ำทะเล'
                ))
            except Exception as e:
                print(f"Error migrating user {user['username']}: {e}")
                pg_conn.rollback()
                continue
    pg_conn.commit()
    print("ย้ายตาราง users เสร็จสิ้น!")

    # --- 2. ตาราง reviews ---
    print("เริ่มย้ายข้อมูลตาราง reviews...")
    sqlite_cur.execute("SELECT * FROM reviews")
    for row in sqlite_cur.fetchall():
        pg_cur.execute("SELECT id FROM reviews WHERE id = %s", (row['id'],))
        if not pg_cur.fetchone():
            pg_cur.execute('''
                INSERT INTO reviews (id, beach_name, username, stars, text, img)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (row['id'], row['beach_name'], row['username'], row['stars'], row['text'], row['img']))
    pg_conn.commit()
    
    # --- 3. ตาราง pinned_locations ---
    print("เริ่มย้ายข้อมูลตาราง pinned_locations...")
    sqlite_cur.execute("SELECT * FROM pinned_locations")
    for row in sqlite_cur.fetchall():
        pg_cur.execute("SELECT id FROM pinned_locations WHERE id = %s", (row['id'],))
        if not pg_cur.fetchone():
            pg_cur.execute('''
                INSERT INTO pinned_locations (id, username, province, place_name, lat, lng, water_quality, mwqi, do_val, tss, ph, comment, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                row['id'], row['username'], row['province'], row['place_name'], row['lat'], row['lng'],
                row['water_quality'], row['mwqi'], row['do_val'], row['tss'], row['ph'], row['comment'], row['status']
            ))
    pg_conn.commit()

    # --- 4. ตาราง pollution_reports ---
    print("เริ่มย้ายข้อมูลตาราง pollution_reports...")
    sqlite_cur.execute("SELECT * FROM pollution_reports")
    for row in sqlite_cur.fetchall():
        pg_cur.execute("SELECT id FROM pollution_reports WHERE id = %s", (row['id'],))
        if not pg_cur.fetchone():
            pg_cur.execute('''
                INSERT INTO pollution_reports (id, username, lat, lng, image_path, trash_count, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                row['id'], row['username'], row['lat'], row['lng'], row['image_path'], 
                row['trash_count'], row['status'], row['created_at']
            ))
    pg_conn.commit()

    # --- 5. ตาราง cleared_reports ---
    print("เริ่มย้ายข้อมูลตาราง cleared_reports...")
    sqlite_cur.execute("SELECT * FROM cleared_reports")
    for row in sqlite_cur.fetchall():
        pg_cur.execute("SELECT id FROM cleared_reports WHERE id = %s", (row['id'],))
        if not pg_cur.fetchone():
            pg_cur.execute('''
                INSERT INTO cleared_reports (id, report_id, username, before_image, after_image, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (
                row['id'], row['report_id'], row['username'], row['before_image'], 
                row['after_image'], row['status'], row['created_at']
            ))
    pg_conn.commit()

    # --- 6. ตาราง votes ---
    print("เริ่มย้ายข้อมูลตาราง votes...")
    sqlite_cur.execute("SELECT * FROM votes")
    for row in sqlite_cur.fetchall():
        pg_cur.execute("SELECT id FROM votes WHERE id = %s", (row['id'],))
        if not pg_cur.fetchone():
            pg_cur.execute('''
                INSERT INTO votes (id, username, target_type, target_id, vote, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                row['id'], row['username'], row['target_type'], row['target_id'], row['vote'], row['created_at']
            ))
    pg_conn.commit()

    # แก้ไข sequence สำหรับ id ใหม่อัตโนมัติใน PostgreSQL
    tables = ['users', 'reviews', 'pinned_locations', 'pollution_reports', 'cleared_reports', 'votes']
    for table in tables:
        pg_cur.execute(f"SELECT setval('{table}_id_seq', (SELECT MAX(id) FROM {table}));")
    pg_conn.commit()

    # ปิดการเชื่อมต่อ
    sqlite_conn.close()
    pg_conn.close()
    print("Migration Complete! โอนย้ายข้อมูลสำเร็จ 100%")

if __name__ == "__main__":
    migrate()
