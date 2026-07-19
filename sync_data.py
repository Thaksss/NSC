import requests
import json
import os

API_KEY = "Q3nfoFvugIUYEKKBcQnlEI23XmMtlPaL"
RESOURCE_ID = "89faffe4-5d67-4443-bfe2-999538ddc670"

def update_cached_data():
    headers = {"api-key": API_KEY}
    search_url = "https://data.go.th/api/3/action/datastore_search"
    params = {
        "resource_id": RESOURCE_ID,
        "limit": 5000  
    }
    
    print("กำลังเชื่อมต่อกับ API ของ data.go.th...")
    try:
        # ใช้ timeout ยาวหน่อยได้ เพราะรันบนเครื่องเราเองไม่ได้ทำให้เว็บค้าง
        response = requests.get(search_url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            res_data = response.json()
            if res_data.get('success'):
                records = res_data['result']['records']
                print(f"ดึงข้อมูลสำเร็จ! ได้รับข้อมูลจำนวน {len(records)} รายการ")
                
                # นำข้อมูลมาบันทึกลงไฟล์ cached_water_data.json
                current_dir = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(current_dir, 'cached_water_data.json')
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(records, f, ensure_ascii=False, indent=2)
                    
                print(f"อัปเดตไฟล์ {file_path} เรียบร้อยแล้ว!")
                print("คุณสามารถ Commit ไฟล์นี้และ Push ขึ้น Render ได้เลยครับ")
            else:
                print("ดึงข้อมูลสำเร็จ แต่ API ส่งค่า success เป็น False")
        else:
            print(f"เกิดข้อผิดพลาดในการดึงข้อมูล HTTP Status: {response.status_code}")
            
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}")

if __name__ == "__main__":
    update_cached_data()
