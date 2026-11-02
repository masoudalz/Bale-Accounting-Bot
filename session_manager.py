# session_manager.py
import json
import os
import time
import requests
from config import WEBZI_BASE_URL, WEBZI_API_HEADERS

COOKIE_FILE = "cookies.json"
SESSION_FILE = "session_data.json"

def login_to_site():
    login_url = "https://example.com/admin/login"
    
    login_data = {
        "username": os.getenv("SITE_USERNAME", "admin"),
        "password": os.getenv("SITE_PASSWORD", "password")
    }
    
    session = requests.Session()
    
    try:
        response = session.post(login_url, data=login_data, timeout=15)
        
        if response.status_code == 200:
            cookies = session.cookies.get_dict()
            with open(COOKIE_FILE, "w") as f:
                json.dump(cookies, f)
            return session
        else:
            print(f"❌ خطا در لاگین: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ خطا در لاگین: {e}")
        return None


def load_saved_cookies():
    if os.path.exists(COOKIE_FILE):
        try:
            with open(COOKIE_FILE, "r") as f:
                cookies = json.load(f)
                return cookies
        except:
            return None
    return None


def get_session_with_retry(max_retries=3):
    session = requests.Session()
    
    saved_cookies = load_saved_cookies()
    if saved_cookies:
        session.cookies.update(saved_cookies)
    
    session.headers.update(WEBZI_API_HEADERS)
    
    for attempt in range(max_retries):
        try:
            test_response = session.get(
                f"{WEBZI_BASE_URL}?page=1", 
                timeout=10
            )
            
            if test_response.status_code == 200:
                return session
            
            if test_response.status_code in [401, 403]:
                print(f"⚠️ کوکی منقضی شده، تلاش برای لاگین مجدد... (تلاش {attempt + 1}/{max_retries})")
                new_session = login_to_site()
                if new_session:
                    session = new_session
                    session.headers.update(WEBZI_API_HEADERS)
                    continue
                else:
                    time.sleep(2)
                    continue
            else:
                print(f"⚠️ خطای غیرمنتظره: {test_response.status_code}")
                time.sleep(2)
                continue
                
        except requests.exceptions.Timeout:
            print("⏳ تایم‌اوت در اتصال به سرور")
            time.sleep(2)
            continue
        except Exception as e:
            print(f"⚠️ خطا: {e}")
            time.sleep(2)
            continue
    
    print("❌ همه تلاش‌ها برای اتصال به سایت ناموفق بود")
    return None


def get_product_price_from_site(code):
    return None


def refresh_cookies_manually():
    print("🔄 در حال به‌روزرسانی کوکی‌ها...")
    session = login_to_site()
    if session:
        print("✅ کوکی‌ها با موفقیت به‌روزرسانی شدند")
        return True
    else:
        print("❌ خطا در به‌روزرسانی کوکی‌ها")
        return False
