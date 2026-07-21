from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests
import sqlite3
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os
import uuid
import base64
import re
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email_validator import validate_email, EmailNotValidError
app = Flask(__name__)
app.secret_key = 'blueheart_secret_key_encryption'

import io
import json

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

WASTE_CLASSES = list(range(12))

API_KEY = "Q3nfoFvugIUYEKKBcQnlEI23XmMtlPaL"
RESOURCE_ID = "89faffe4-5d67-4443-bfe2-999538ddc670" 

import time
WATER_QUALITY_CACHE = None
LAST_CACHE_TIME = 0
CACHE_DURATION_SECONDS = 3600 * 24 # 1 day

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    try:
        conn.execute('ALTER TABLE users ADD COLUMN score INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass
        
    try:
        conn.execute('ALTER TABLE users ADD COLUMN rank TEXT DEFAULT "หยาดน้ำทะเล"')
    except sqlite3.OperationalError:
        pass
        
    try:
        conn.execute('ALTER TABLE users ADD COLUMN role TEXT DEFAULT "user"')
    except sqlite3.OperationalError:
        pass
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            beach_name TEXT NOT NULL,
            username TEXT NOT NULL,
            stars INTEGER NOT NULL,
            text TEXT NOT NULL,
            img TEXT
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS pinned_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            province TEXT NOT NULL,
            place_name TEXT NOT NULL,
            lat TEXT NOT NULL,
            lng TEXT NOT NULL,
            water_quality TEXT,
            mwqi TEXT,
            do_val TEXT,
            tss TEXT,
            ph TEXT,
            comment TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS pollution_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            lat TEXT NOT NULL,
            lng TEXT NOT NULL,
            image_path TEXT NOT NULL,
            trash_count INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS cleared_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            before_image TEXT NOT NULL,
            after_image TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            target_type TEXT NOT NULL,
            target_id INTEGER NOT NULL,
            vote TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(username, target_type, target_id)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

def get_water_quality_records():
    global WATER_QUALITY_CACHE, LAST_CACHE_TIME
    
    if WATER_QUALITY_CACHE is not None and (time.time() - LAST_CACHE_TIME < CACHE_DURATION_SECONDS):
        return WATER_QUALITY_CACHE
        
    records = None
    cache_path = os.path.join(os.path.dirname(__file__), 'cached_water_data.json')
    if os.path.exists(cache_path):
        try:
            import json
            with open(cache_path, 'r', encoding='utf-8') as f:
                records = json.load(f)
            print(f"โหลดข้อมูลจากไฟล์สำรอง (Sync Data) สำเร็จ ({len(records)} รายการ)")
        except Exception as cache_err:
            print(f"ไม่สามารถโหลดข้อมูลจากไฟล์สำรองได้: {cache_err}")
    else:
        print("ไม่พบไฟล์ข้อมูลคุณภาพน้ำ กรุณารัน sync_data.py ก่อน")
                
    if not records:
        return []
        
    records = sorted(records, key=lambda x: x.get('date', ''))
    
    formatted_beaches = []
    for row in records:
        try:
            lat = float(row.get('latitude')) if row.get('latitude') else None
            lng = float(row.get('longitude')) if row.get('longitude') else None
        except ValueError:
            lat, lng = None, None

        if lat and lng:
            soway_class = row.get('soway_class', 'ไม่ทราบพารามิเตอร์')
            
            color = "#2ecc71"
            if "พอใช้" in soway_class:
                color = "#f1c40f"
            elif "เสื่อมโทรม" in soway_class:
                color = "#e74c3c"

            beach_info = {
                "beach_name": row.get('area_name', 'ไม่ระบุชื่อ'),
                "station_code": row.get('station', 'ไม่ระบุสถานี'),
                "province": row.get('province', 'ไม่ระบุจังหวัด'),
                "lat": lat,
                "lng": lng,
                "status": soway_class,
                "mwqi": row.get('soway_score', '-'),
                "color": color,
                "do_val": row.get('dissolved_oxygen_mg_l', '-'),
                "salinity": row.get('salinity_ppt', '-'),
                "tss": row.get('total_suspended_solids_mg_l', '-'),
                "ph": row.get('ph', '-'),
                "date": row.get('date', ''),
                "year": row.get('date', '2021').split('-')[0]
            }
            formatted_beaches.append(beach_info)
            
    WATER_QUALITY_CACHE = formatted_beaches
    LAST_CACHE_TIME = time.time()
    return formatted_beaches

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
def home():
    all_beaches_data = get_water_quality_records()
    
    latest_beaches_only = []
    seen_beaches = set()
    
    for beach in reversed(all_beaches_data):
        unique_key = f"{beach['beach_name']}_{beach['province']}"
        if unique_key not in seen_beaches:
            seen_beaches.add(unique_key)
            latest_beaches_only.append(beach)
            
    unique_provinces = sorted(list(set(beach['province'] for beach in latest_beaches_only if beach.get('province'))))
            
    return render_template("home.html", beaches=latest_beaches_only, provinces=unique_provinces)

@app.route('/pdata')
def pdata():
    all_beaches_data = get_water_quality_records()
    return render_template("pdata.html", beaches=all_beaches_data)

@app.route('/pin', methods=['GET', 'POST'])
def piautihighlign():
    all_beaches_data = get_water_quality_records()
    unique_provinces = sorted(list(set(beach['province'] for beach in all_beaches_data if beach.get('province'))))
    
    if not session.get('username'):
        return redirect(url_for('login')) 
        
    if request.method == 'POST':
        coordinates = request.form.get('coordinates')
        place_name = request.form.get('place_name') 
        province = request.form.get('province')

        water_quality = request.form.get('water_quality')
        mwqi = request.form.get('mwqi')
        do_val = request.form.get('do_val')
        tss = request.form.get('tss')
        ph = request.form.get('ph')
        comment = request.form.get('comment')
        
        lat, lng = "", ""
        if coordinates:
            lat, lng = coordinates.split(',')
            lat = lat.strip()
            lng = lng.strip()

        try:
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO pinned_locations (username, province, place_name, lat, lng, water_quality, mwqi, do_val, tss, ph, comment) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session['username'], province, place_name, lat, lng, water_quality, mwqi, do_val, tss, ph, comment))
            conn.commit()
        except Exception as e:
            print(f"Error inserting pin: {e}")
        finally:
            conn.close()
            
        print(f"ได้รับข้อมูลจุดปักหมุดใหม่จากคุณ {session['username']}: {place_name}, พิกัด: {coordinates}")
        
        return redirect(url_for('home'))

    return render_template("pin.html", provinces=unique_provinces)

@app.route('/game')
def game():
    conn = get_db_connection()
    top_users = conn.execute('SELECT username, score, rank FROM users ORDER BY score DESC LIMIT 10').fetchall()
    conn.close()
    return render_template('game.html', leaderboard=top_users)

@app.route('/ingame')
def ingame():
    if not session.get('username'):
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (session['username'],)).fetchone()
    conn.close()
    
    if user:
        score = user['score'] if 'score' in user.keys() else 0
        rank = user['rank'] if 'rank' in user.keys() else "หยาดน้ำทะเล"
    else:
        score = 0
        rank = "หยาดน้ำทะเล"
        
    return render_template('ingame.html', username=session['username'], score=score, rank=rank)

@app.route('/history')
def history():
    if not session.get('username'):
        return redirect(url_for('login'))
        
    username = session['username']
    conn = get_db_connection()
    
    reports = conn.execute('SELECT * FROM pollution_reports WHERE username = ? ORDER BY created_at DESC', (username,)).fetchall()
    
    clears = conn.execute('SELECT * FROM cleared_reports WHERE username = ? ORDER BY created_at DESC', (username,)).fetchall()
    
    votes = conn.execute('''
        SELECT v.*, 
               p.image_path as report_img, 
               c.before_image as clear_before, 
               c.after_image as clear_after
        FROM votes v
        LEFT JOIN pollution_reports p ON v.target_type = 'report' AND v.target_id = p.id
        LEFT JOIN cleared_reports c ON v.target_type = 'clear' AND v.target_id = c.id
        WHERE v.username = ? 
        ORDER BY v.created_at DESC
    ''', (username,)).fetchall()
    
    conn.close()
    
    return render_template('history.html', reports=reports, clears=clears, votes=votes)

@app.route('/report')
def report():
    return render_template('report.html')

@app.route('/clear')
def clear():
    conn = get_db_connection()
    reports = conn.execute('SELECT * FROM pollution_reports WHERE status = "approved"').fetchall()
    
    pending_clears = conn.execute('SELECT report_id FROM cleared_reports WHERE status = "pending"').fetchall()
    pending_ids = [r['report_id'] for r in pending_clears]
    
    conn.close()
    
    approved_reports = []
    for r in reports:
        approved_reports.append({
            'id': r['id'],
            'username': r['username'],
            'lat': r['lat'],
            'lng': r['lng'],
            'image_path': r['image_path'],
            'created_at': r['created_at'],
            'is_pending_clear': r['id'] in pending_ids
        })
        
    return render_template('clear.html', reports=approved_reports)

@app.route('/inclear/<int:report_id>')
def inclear(report_id):
    if not session.get('username'):
        return redirect(url_for('login'))
    return render_template('inclear.html', report_id=report_id)

@app.route('/submit_clear_report', methods=['POST'])
def submit_clear_report():
    if 'username' not in session:
        return jsonify({"success": False, "message": "กรุณาเข้าสู่ระบบก่อน"}), 401
        
    data = request.json
    report_id = data.get('report_id')
    before_base64 = data.get('before_image')
    after_base64 = data.get('after_image')
    
    if not all([report_id, before_base64, after_base64]):
        return jsonify({"success": False, "message": "ข้อมูลไม่ครบถ้วน"}), 400
        
    upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'cleared')
    os.makedirs(upload_dir, exist_ok=True)
    
    try:
        before_filename = f"before_{uuid.uuid4().hex}.jpg"
        before_filepath = os.path.join(upload_dir, before_filename)
        b_data = before_base64.split(",")[1] if "," in before_base64 else before_base64
        with open(before_filepath, "wb") as fh:
            fh.write(base64.b64decode(b_data))
            
        after_filename = f"after_{uuid.uuid4().hex}.jpg"
        after_filepath = os.path.join(upload_dir, after_filename)
        a_data = after_base64.split(",")[1] if "," in after_base64 else after_base64
        with open(after_filepath, "wb") as fh:
            fh.write(base64.b64decode(a_data))
            
    except Exception as e:
        print(f"Error saving cleared images: {e}")
        return jsonify({"success": False, "message": "เกิดข้อผิดพลาดในการบันทึกรูปภาพ"}), 500
        
    try:
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO cleared_reports (report_id, username, before_image, after_image, status)
            VALUES (?, ?, ?, ?, 'pending')
        ''', (report_id, session['username'], f'static/uploads/cleared/{before_filename}', f'static/uploads/cleared/{after_filename}'))
        conn.commit()
    except Exception as e:
        print(f"Error inserting cleared report: {e}")
        return jsonify({"success": False, "message": "เกิดข้อผิดพลาดในการบันทึกข้อมูลลงฐานข้อมูล"}), 500
    finally:
        conn.close()
        
    return jsonify({"success": True, "message": "ส่งข้อมูลการเคลียร์มลพิษสำเร็จ รอแอดมินตรวจสอบ"})

def send_otp_email(to_email, otp):
    EMAIL_ADDRESS = "heartblue172@gmail.com" 
    MAILJET_API_KEY = "7f87768e78b86fd2d3eec322d638e451"
    MAILJET_API_SECRET = "156defb98f10d5cbda36b9c2df7b3670"
    
    print(f"\n--- [SYSTEM] OTP for {to_email} is: {otp} ---\n")
    
    url = "https://api.mailjet.com/v3.1/send"
    data = {
        "Messages": [
            {
                "From": {
                    "Email": EMAIL_ADDRESS,
                    "Name": "Blue Heart"
                },
                "To": [
                    {
                        "Email": to_email
                    }
                ],
                "Subject": "รหัสยืนยัน OTP สำหรับการสมัครสมาชิก/กู้คืนรหัสผ่าน",
                "TextPart": f"รหัสยืนยัน OTP ของคุณคือ: {otp}\nรหัสนี้จะหมดอายุภายใน 5 นาที",
                "HTMLPart": f"<h3>รหัสยืนยัน OTP ของคุณคือ: <strong>{otp}</strong></h3><br/>รหัสนี้จะหมดอายุภายใน 5 นาที"
            }
        ]
    }
    
    try:
        response = requests.post(url, auth=(MAILJET_API_KEY, MAILJET_API_SECRET), json=data, timeout=10)
        if response.status_code == 200:
            print("Email sent successfully via Mailjet!")
            return True
        else:
            print(f"Failed to send email via Mailjet: {response.status_code} {response.text}")
            return False
    except Exception as e:
        print(f"Failed to send email via Mailjet request: {e}")
        return False

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user:
            otp = ''.join(random.choices(string.digits, k=6))
            session['reset_email'] = email
            session['reset_otp'] = otp
            is_sent = send_otp_email(email, otp)
            return render_template('forgot-password.html', step='otp', dev_otp=otp if not is_sent else None)
        else:
            return render_template('forgot-password.html', error="ไม่พบอีเมลนี้ในระบบ")
            
    return render_template('forgot-password.html')

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    otp_input = request.form.get('otp')
    if otp_input and otp_input == session.get('reset_otp'):
        return render_template('forgot-password.html', step='reset')
    else:
        return render_template('forgot-password.html', step='otp', error="รหัส OTP ไม่ถูกต้อง")

@app.route('/reset-password', methods=['POST'])
def reset_password():
    password = request.form.get('password')
    email = session.get('reset_email')
    
    if not email:
        return redirect(url_for('forgot_password'))
        
    if len(password) < 6 or not re.search(r'[a-zA-Z]', password):
        return render_template('forgot-password.html', step='reset', error="รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษรและต้องมีตัวอักษรภาษาอังกฤษ")
        
    hashed_password = generate_password_hash(password)
    
    conn = get_db_connection()
    conn.execute('UPDATE users SET password = ? WHERE email = ?', (hashed_password, email))
    conn.commit()
    conn.close()
    
    session.pop('reset_email', None)
    session.pop('reset_otp', None)
    
    print(f"รหัสผ่านใหม่ถูกตั้งค่าสำหรับอีเมล: {email}")
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_input = request.form.get('username')
        password_input = request.form.get('password')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? OR email = ?', 
                            (username_input, username_input)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password_input):
            session['username'] = user['username']
            
            if user['username'] == 'Thak' and user['email'] == 'skillrodchan@gmail.com':
                conn_admin = get_db_connection()
                conn_admin.execute("UPDATE users SET role = 'admin' WHERE id = ?", (user['id'],))
                conn_admin.commit()
                conn_admin.close()
                session['role'] = 'admin'
            else:
                session['role'] = user['role'] if 'role' in user.keys() else 'user'
                
            print(f"เข้าสู่ระบบสำเร็จ: {user['username']} (Role: {session.get('role')})")
            return redirect(url_for('home'))
        else:
            print("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
            return render_template('login.html', error="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if len(password) < 6 or not re.search(r'[a-zA-Z]', password):
            return render_template('register.html', error="รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษรและต้องมีตัวอักษรภาษาอังกฤษ")
            
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError as e:
            return render_template('register.html', error="อีเมลนี้ไม่มีอยู่จริง หรือรูปแบบไม่ถูกต้อง")
        
        conn = get_db_connection()
        existing_user = conn.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email)).fetchone()
        conn.close()
        
        if existing_user:
            return render_template('register.html', error="ชื่อผู้ใช้หรืออีเมลนี้มีอยู่ในระบบแล้ว")
            
        hashed_password = generate_password_hash(password)
        
        otp = ''.join(random.choices(string.digits, k=6))
        session['reg_username'] = username
        session['reg_email'] = email
        session['reg_password'] = hashed_password
        session['reg_otp'] = otp
        
        is_sent = send_otp_email(email, otp)
        
        return render_template('register.html', step='otp', dev_otp=otp if not is_sent else None)
            
    return render_template('register.html')

@app.route('/verify-register-otp', methods=['POST'])
def verify_register_otp():
    otp_input = request.form.get('otp')
    
    if otp_input and otp_input == session.get('reg_otp'):
        username = session.get('reg_username')
        email = session.get('reg_email')
        hashed_password = session.get('reg_password')
        
        if not all([username, email, hashed_password]):
            return render_template('register.html', error="ข้อมูลเซสชันสูญหาย กรุณาสมัครสมาชิกใหม่")
            
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                         (username, email, hashed_password))
            conn.commit()
            conn.close()
            
            session.pop('reg_username', None)
            session.pop('reg_email', None)
            session.pop('reg_password', None)
            session.pop('reg_otp', None)
            
            session['username'] = username 
            print(f"สมัครสมาชิกใหม่สำเร็จ (OTP): {username}")
            return redirect(url_for('home'))
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('register.html', error="เกิดข้อผิดพลาด ชื่อผู้ใช้หรืออีเมลนี้ถูกใช้ไปแล้ว")
    else:
        return render_template('register.html', step='otp', error="รหัส OTP ไม่ถูกต้อง")

@app.route('/resend-register-otp', methods=['GET', 'POST'])
def resend_register_otp():
    email = session.get('reg_email')
    if not email:
        return redirect(url_for('register'))
        
    otp = ''.join(random.choices(string.digits, k=6))
    session['reg_otp'] = otp
    is_sent = send_otp_email(email, otp)
    
    msg = "ระบบได้ส่งรหัส OTP ใหม่ไปยังอีเมลของคุณแล้ว" if is_sent else "ไม่สามารถส่งอีเมลได้ กรุณาใช้รหัสสำรองด้านล่าง"
    return render_template('register.html', step='otp', error=msg, dev_otp=otp if not is_sent else None)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    print("ผู้ใช้ออกจากระบบแล้ว")
    return redirect(url_for('index'))

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'username' not in session:
        print("ยังไม่ได้ล็อกอิน ไม่สามารถลบบัญชีได้")
        return redirect(url_for('login'))
        
    username_to_delete = session['username']
    
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM users WHERE username = ?', (username_to_delete,))
        conn.commit()
        conn.close()
        
        session.pop('username', None)
        session.pop('role', None)
        print(f"ลบบัญชีผู้ใช้ {username_to_delete} เรียบร้อยแล้ว")
        
        return redirect(url_for('index'))
        
    except Exception as e:
        if conn:
            conn.close()
        print(f"เกิดข้อผิดพลาดในการลบบัญชี: {e}")
        return "เกิดข้อผิดพลาดในการลบบัญชี กรุณาลองใหม่อีกครั้ง"

@app.route('/submit_review', methods=['POST'])
def submit_review():
    if 'username' not in session:
        return {"status": "error", "message": "กรุณาเข้าสู่ระบบก่อนรีวิวสถานที่ครับ"}, 401
        
    data = request.json
    beach_name = data.get('beach_name')
    stars = data.get('stars')
    text = data.get('text')
    img = data.get('img') 

    if not text:
        return {"status": "error", "message": "กรุณากรอกข้อความรีวิว"}, 400

    conn = get_db_connection()
    conn.execute('INSERT INTO reviews (beach_name, username, stars, text, img) VALUES (?, ?, ?, ?, ?)',
                 (beach_name, session['username'], stars, text, img))
    conn.commit()
    conn.close()
    
    return {"status": "success", "message": "บันทึกรีวิวสำเร็จเรียบร้อย!"}

@app.route('/delete_review/<int:review_id>', methods=['POST'])
def delete_review(review_id):
    if 'username' not in session:
        return {"status": "error", "message": "กรุณาเข้าสู่ระบบก่อนทำรายการ"}, 401
        
    conn = get_db_connection()
    review = conn.execute('SELECT * FROM reviews WHERE id = ?', (review_id,)).fetchone()
    
    if not review:
        conn.close()
        return {"status": "error", "message": "ไม่พบรีวิวดังกล่าว"}, 404
        
    if review['username'] != session['username']:
        conn.close()
        return {"status": "error", "message": "คุณไม่มีสิทธิ์ลบรีวิวของผู้อื่น"}, 403

    conn.execute('DELETE FROM reviews WHERE id = ?', (review_id,))
    conn.commit()
    conn.close()
    
    return {"status": "success", "message": "ลบรีวิวเรียบร้อยแล้ว!"}

@app.route('/get_reviews/<path:beach_name>', methods=['GET'])
def get_reviews(beach_name):
    conn = get_db_connection()
    reviews = conn.execute('SELECT * FROM reviews WHERE beach_name = ? ORDER BY id DESC', (beach_name,)).fetchall()
    conn.close()
    
    output = []
    for row in reviews:
        output.append({
            "id": row['id'],
            "user": row['username'],
            "stars": row['stars'],
            "text": row['text'],
            "img": row['img'] 
        })
        
    return {"reviews": output}

@app.route("/api/detect-trash", methods=["POST"])
def detect_trash():
    if 'image' not in request.files:
        return jsonify({"error": "No image provided"}), 400
        
    file_content = request.files['image'].read()
    
    try:
        if not GEMINI_API_KEY:
            return jsonify({
                "success": False,
                "message": "Gemini API Key is not set in Environment Variables."
            })
            
        # Use Gemini REST API
        import base64
        
        base64_img = base64.b64encode(file_content).decode('utf-8')
        
        prompt = """
        Analyze this image and detect if there is any trash/waste.
        Count the number of trash items and list the type of trash items detected.
        Respond ONLY with a valid JSON in this exact format:
        {"total_pieces": 5, "items": ["plastic bottle", "plastic bag", "can"]}
        If no trash is found, return {"total_pieces": 0, "items": []}
        """
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": base64_img
                        }
                    }
                ]
            }]
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"API Error {response.status_code}: {response.text}")
            
        result_json = response.json()
        
        try:
            text = result_json['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError) as e:
            raise Exception("Unexpected response structure from Gemini API")
            
        # Clean up markdown formatting if present
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
            
        data = json.loads(text)
        data["success"] = True
        return jsonify(data)
            
    except Exception as e:
        import traceback
        print(f"Detect Trash Error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Gemini Error: {str(e)}"
        })

@app.route('/submit_pollution_report', methods=['POST'])
def submit_pollution_report():
    if 'username' not in session:
        return jsonify({"success": False, "message": "กรุณาเข้าสู่ระบบก่อน"}), 401
        
    data = request.json
    image_base64 = data.get('image')
    lat = data.get('lat')
    lng = data.get('lng')
    trash_count = data.get('trash_count')
    
    if not all([image_base64, lat, lng, trash_count is not None]):
        return jsonify({"success": False, "message": "ข้อมูลไม่ครบถ้วน"}), 400
        
    upload_dir = os.path.join(app.root_path, 'static', 'uploads', 'reports')
    os.makedirs(upload_dir, exist_ok=True)
    
    filename = f"{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(upload_dir, filename)
    
    try:
        if "," in image_base64:
            image_data = image_base64.split(",")[1]
        else:
            image_data = image_base64
        with open(filepath, "wb") as fh:
            fh.write(base64.b64decode(image_data))
    except Exception as e:
        print(f"Error saving image: {e}")
        return jsonify({"success": False, "message": "เกิดข้อผิดพลาดในการบันทึกรูปภาพ"}), 500
        
    try:
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO pollution_reports (username, lat, lng, image_path, trash_count, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        ''', (session['username'], lat, lng, f'static/uploads/reports/{filename}', trash_count))
        conn.commit()
    except Exception as e:
        print(f"Error inserting report: {e}")
        return jsonify({"success": False, "message": "เกิดข้อผิดพลาดในการบันทึกข้อมูลลงฐานข้อมูล"}), 500
    finally:
        conn.close()
        
    return jsonify({"success": True, "message": "ส่งรายงานสำเร็จ อยู่ในขั้นตอนหลังบ้านตรวจ"})

@app.route('/confirm')
def confirm_page():
    if not session.get('username'):
        return redirect(url_for('login'))
        
    username = session['username']
    conn = get_db_connection()
    
    all_reports = conn.execute('SELECT * FROM pollution_reports WHERE status = "pending"').fetchall()
    
    all_clears = conn.execute('''
        SELECT c.*, p.lat, p.lng 
        FROM cleared_reports c
        JOIN pollution_reports p ON c.report_id = p.id
        WHERE c.status = "pending"
    ''').fetchall()

    user_votes = conn.execute('SELECT target_type, target_id FROM votes WHERE username = ?', (username,)).fetchall()
    voted_reports = [v['target_id'] for v in user_votes if v['target_type'] == 'report']
    voted_clears = [v['target_id'] for v in user_votes if v['target_type'] == 'clear']
    
    conn.close()
    
    unvoted_reports = [dict(r) for r in all_reports if r['id'] not in voted_reports]
    unvoted_clears = [dict(c) for c in all_clears if c['id'] not in voted_clears]
    
    return render_template('confirm.html', reports=unvoted_reports, clears=unvoted_clears)

@app.route('/submit_vote', methods=['POST'])
def submit_vote():
    if 'username' not in session:
        return jsonify({"success": False, "message": "กรุณาเข้าสู่ระบบก่อน"}), 401
        
    data = request.json
    target_type = data.get('target_type')
    target_id = data.get('target_id')
    vote = data.get('vote')
    
    if not all([target_type, target_id, vote]):
        return jsonify({"success": False, "message": "ข้อมูลไม่ครบถ้วน"}), 400
        
    try:
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO votes (username, target_type, target_id, vote)
            VALUES (?, ?, ?, ?)
        ''', (session['username'], target_type, target_id, vote))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "คุณได้ทำการโหวตรายการนี้ไปแล้ว"})
    except Exception as e:
        print(f"Error submitting vote: {e}")
        return jsonify({"success": False, "message": "เกิดข้อผิดพลาดในการบันทึกข้อมูล"}), 500
    finally:
        conn.close()
        
    return jsonify({"success": True, "message": "บันทึกผลโหวตสำเร็จ!"})

@app.route('/admin/reports')
def admin_reports():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
        
    conn = get_db_connection()
    reports = conn.execute('SELECT * FROM pollution_reports WHERE status = "pending" ORDER BY created_at DESC').fetchall()
    cleared_reports = conn.execute('SELECT * FROM cleared_reports WHERE status = "pending" ORDER BY created_at DESC').fetchall()
    
    vote_rows = conn.execute('SELECT target_type, target_id, vote, COUNT(*) as count FROM votes GROUP BY target_type, target_id, vote').fetchall()
    conn.close()
    
    vote_data = {'report': {}, 'clear': {}}
    for row in vote_rows:
        t_type = row['target_type']
        t_id = row['target_id']
        t_vote = row['vote']
        
        if t_id not in vote_data[t_type]:
            vote_data[t_type][t_id] = {'pass': 0, 'fail': 0}
            
        vote_data[t_type][t_id][t_vote] = row['count']
        
    return render_template('admin_reports.html', reports=reports, cleared_reports=cleared_reports, vote_data=vote_data)

@app.route('/admin/approve_report/<int:report_id>', methods=['POST'])
def approve_report(report_id):
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
        
    try:
        conn = get_db_connection()
        report = conn.execute('SELECT * FROM pollution_reports WHERE id = ?', (report_id,)).fetchone()
        if report and report['status'] == 'pending':
            conn.execute('UPDATE pollution_reports SET status = "approved" WHERE id = ?', (report_id,))
            conn.execute('UPDATE users SET score = score + 2 WHERE username = ?', (report['username'],))
            conn.commit()
    except Exception as e:
        print(f"Error approving report: {e}")
    finally:
        conn.close()
    return redirect(url_for('admin_reports'))

@app.route('/admin/reject_report/<int:report_id>', methods=['POST'])
def reject_report(report_id):
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
        
    try:
        conn = get_db_connection()
        conn.execute('UPDATE pollution_reports SET status = "rejected" WHERE id = ?', (report_id,))
        conn.commit()
    except Exception as e:
        print(f"Error rejecting report: {e}")
    finally:
        conn.close()
    return redirect(url_for('admin_reports'))

@app.route('/admin/approve_clear/<int:clear_id>', methods=['POST'])
def approve_clear(clear_id):
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
        
    try:
        conn = get_db_connection()
        clear_report = conn.execute('SELECT * FROM cleared_reports WHERE id = ?', (clear_id,)).fetchone()
        if clear_report and clear_report['status'] == 'pending':
            conn.execute('UPDATE cleared_reports SET status = "approved" WHERE id = ?', (clear_id,))
            conn.execute('UPDATE pollution_reports SET status = "cleared" WHERE id = ?', (clear_report['report_id'],))
            conn.execute('UPDATE users SET score = score + 5 WHERE username = ?', (clear_report['username'],))
            conn.commit()
    except Exception as e:
        print(f"Error approving clear: {e}")
    finally:
        conn.close()
    return redirect(url_for('admin_reports'))

@app.route('/admin/reject_clear/<int:clear_id>', methods=['POST'])
def reject_clear(clear_id):
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
        
    try:
        conn = get_db_connection()
        conn.execute('UPDATE cleared_reports SET status = "rejected" WHERE id = ?', (clear_id,))
        conn.commit()
    except Exception as e:
        print(f"Error rejecting clear: {e}")
    finally:
        conn.close()
    return redirect(url_for('admin_reports'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)