# bot_handlers.py
import time
import json
import requests
from config import BASE_URL, PASSWORD_NORMAL, PASSWORD_FULL, PASSWORD_WAREHOUSE
from utils import send_message, send_message_with_buttons, answer_callback
from services import (send_main_menu, send_full_menu, send_warehouse_menu, send_main_menu_buttons, 
                      send_full_menu_buttons, send_warehouse_menu_buttons, send_stock_results, 
                      send_statement_as_pdf, send_all_today_invoices, search_invoice_by_number)
from database import search_products, search_person_for_statement

active_users = set()
user_search_state = {}
user_statement_results = {}
user_temp_data = {}
user_auth_state = {}


def get_access_level(chat_id):
    auth_info = user_auth_state.get(chat_id, {})
    return auth_info.get("access_level", None)


def is_user_authenticated(chat_id):
    auth_info = user_auth_state.get(chat_id, {})
    return auth_info.get("authenticated", False)


def can_access_invoices(chat_id):
    access_level = get_access_level(chat_id)
    return access_level == "full"


def can_access_warehouse(chat_id):
    access_level = get_access_level(chat_id)
    return access_level in ["warehouse", "full"]


def reset_user_auth(chat_id):
    if chat_id in user_auth_state:
        del user_auth_state[chat_id]


def reset_all_user_states(chat_id):
    reset_user_auth(chat_id)
    user_search_state.pop(chat_id, None)
    user_temp_data.pop(chat_id, None)
    user_statement_results.pop(chat_id, None)


def authenticate_user(chat_id, entered_password):
    auth_info = user_auth_state.get(chat_id, {"authenticated": False, "attempts": 0, "access_level": None})
    
    if entered_password == PASSWORD_FULL:
        auth_info["authenticated"] = True
        auth_info["attempts"] = 0
        auth_info["access_level"] = "full"
        user_auth_state[chat_id] = auth_info
        return "full"
    elif entered_password == PASSWORD_WAREHOUSE:
        auth_info["authenticated"] = True
        auth_info["attempts"] = 0
        auth_info["access_level"] = "warehouse"
        user_auth_state[chat_id] = auth_info
        return "warehouse"
    elif entered_password == PASSWORD_NORMAL:
        auth_info["authenticated"] = True
        auth_info["attempts"] = 0
        auth_info["access_level"] = "normal"
        user_auth_state[chat_id] = auth_info
        return "normal"
    else:
        auth_info["attempts"] = auth_info.get("attempts", 0) + 1
        user_auth_state[chat_id] = auth_info
        return None


def get_remaining_attempts(chat_id):
    auth_info = user_auth_state.get(chat_id, {})
    attempts = auth_info.get("attempts", 0)
    return max(0, 3 - attempts)


def send_auth_prompt(chat_id):
    send_message(chat_id, "🔐 به ربات حسابداری خوش آمدید!\n\n"
                          "لطفاً رمز عبور خود را با اعداد (انگلیسی) وارد کنید:")


def send_menu_by_access_level(chat_id):
    access_level = get_access_level(chat_id)
    if access_level == "full":
        send_full_menu(chat_id)
    elif access_level == "warehouse":
        send_warehouse_menu(chat_id)
    else:
        send_main_menu(chat_id)


def get_access_level_name(access_level):
    names = {
        "full": "کامل",
        "warehouse": "انبار",
        "normal": "عادی"
    }
    return names.get(access_level, "نامشخص")


def process_callback_query(update, chat_id, cb_id, action):
    answer_callback(cb_id)
    
    if not is_user_authenticated(chat_id):
        send_auth_prompt(chat_id)
        return
    
    access_level = get_access_level(chat_id)
    
    if action == "search_invoice":
        if access_level in ["full", "normal"]:
            user_search_state[chat_id] = "waiting_for_invoice_search"
            send_message(chat_id, "🔍 لطفاً شماره فاکتور مورد نظر را وارد کنید:")
        else:
            send_message(chat_id, "❌ شما دسترسی به جستجوی فاکتور را ندارید.")
            send_menu_by_access_level(chat_id)
    
    elif action == "search_stock":
        user_search_state[chat_id] = "waiting_for_stock"
        send_message(chat_id, "🔍 لطفاً نام یا کد کالا را وارد کنید:")
    
    elif action == "search_statement":
        user_search_state[chat_id] = "waiting_for_statement"
        send_message(chat_id, "💰 لطفاً نام مشتری را برای مشاهده صورتحساب وارد کنید:")
    
    elif action == "today_invoices":
        if can_access_warehouse(chat_id):
            send_all_today_invoices(chat_id, access_level)
        else:
            send_message(chat_id, "❌ شما دسترسی مشاهده فاکتورهای فروش را ندارید.")
            send_menu_by_access_level(chat_id)
    
    else:
        send_message(chat_id, "❌ گزینه نامعتبر است. لطفاً مجدداً تلاش کنید.")
        send_menu_by_access_level(chat_id)


def process_message(chat_id, text):
    if not is_user_authenticated(chat_id):
        if text == "/start":
            reset_all_user_states(chat_id)
            send_auth_prompt(chat_id)
            return
        
        remaining = get_remaining_attempts(chat_id)
        if remaining > 0:
            result = authenticate_user(chat_id, text)
            if result:
                access_name = get_access_level_name(result)
                send_message(chat_id, f"✅ رمز عبور صحیح است! سطح دسترسی: {access_name}")
                send_menu_by_access_level(chat_id)
            else:
                remaining = get_remaining_attempts(chat_id)
                if remaining > 0:
                    send_message(chat_id, f"❌ رمز عبور اشتباه است!\nتعداد دفعات باقی‌مانده: {remaining}\nلطفاً رمز صحیح را وارد کنید:")
                else:
                    send_message(chat_id, "🔒 تعداد دفعات وارد کردن رمز به پایان رسیده است.\nلطفاً با /start مجدداً تلاش کنید.")
                    reset_all_user_states(chat_id)
        else:
            send_message(chat_id, "🔒 تعداد دفعات وارد کردن رمز به پایان رسیده است.\nلطفاً با /start مجدداً تلاش کنید.")
            reset_all_user_states(chat_id)
        return
    
    current_state = user_search_state.get(chat_id)
    access_level = get_access_level(chat_id)
    
    if text == "/start":
        reset_all_user_states(chat_id)
        send_auth_prompt(chat_id)
        return
    
    if chat_id in user_statement_results:
        if text.isdigit():
            idx = int(text) - 1
            results = user_statement_results[chat_id]
            if 0 <= idx < len(results):
                person = results[idx]
                del user_statement_results[chat_id]
                send_statement_as_pdf(chat_id, person['code'], person['name'], access_level)
            else:
                send_message(chat_id, "❌ شماره نامعتبر است. لطفاً مجدداً شماره ردیف صحیح را ارسال کنید.")
        else:
            send_message(chat_id, "❌ لطفاً یک شماره ردیف عددی معتبر ارسال کنید.")
        return
    
    if current_state == "waiting_for_invoice_search":
        if access_level in ["full", "normal"]:
            user_search_state.pop(chat_id, None)
            search_invoice_by_number(chat_id, text, access_level)
        else:
            user_search_state.pop(chat_id, None)
            send_message(chat_id, "❌ شما دسترسی به جستجوی فاکتور را ندارید.")
            send_menu_by_access_level(chat_id)
        return
    
    if current_state == "waiting_for_stock":
        user_search_state.pop(chat_id, None)
        products = search_products(text)
        send_stock_results(chat_id, products, text, access_level)
        return
    
    if current_state == "waiting_for_statement":
        user_search_state.pop(chat_id, None)
        results = search_person_for_statement(text)
        
        if not results:
            if access_level == "full":
                send_full_menu_buttons(chat_id, f"❌ هیچ شخص دارای سابقه‌ای با نام '{text}' یافت نشد.")
            elif access_level == "warehouse":
                send_warehouse_menu_buttons(chat_id, f"❌ هیچ شخص دارای سابقه‌ای با نام '{text}' یافت نشد.")
            else:
                send_main_menu_buttons(chat_id, f"❌ هیچ شخص دارای سابقه‌ای با نام '{text}' یافت نشد.")
        elif len(results) == 1:
            person = results[0]
            send_statement_as_pdf(chat_id, person['code'], person['name'], access_level)
        else:
            message = f"🔍 {len(results)} نتیجه برای '{text}' یافت شد:\n\n"
            for i, person in enumerate(results, 1):
                message += f"{i} - {person['name']} (کد: {person['code']})\n"
            message += f"\n📌 لطفاً شماره ردیف شخص مورد نظر را ارسال کنید:"
            user_statement_results[chat_id] = results
            send_message(chat_id, message)
        return
    
    send_menu_by_access_level(chat_id)


def run_bot(signals_object=None):
    if signals_object:
        signals_object.log_signal.emit("🤖 ربات در حال اجراست...")
    else:
        print("🤖 ربات در حال اجراست...")
    
    try:
        requests.get(f"{BASE_URL}/deleteWebhook", verify=False, timeout=5)
    except:
        pass
        
    last_update = 0
    
    while True:
        try:
            url = f"{BASE_URL}/getUpdates"
            params = {"timeout": 30, "offset": last_update + 1}
            response = requests.get(url, params=params, verify=False, timeout=35)
            data = response.json()
            
            if data.get("ok") and data.get("result"):
                if signals_object:
                    signals_object.status_signal.emit(True)
                    
                for update in data["result"]:
                    last_update = update["update_id"]
                    
                    if "callback_query" in update:
                        cb = update["callback_query"]
                        chat_id = cb["message"]["chat"]["id"]
                        cb_id = cb["id"]
                        action = cb.get("data")
                        process_callback_query(update, chat_id, cb_id, action)
                        continue
                    
                    if "message" in update:
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        text = msg.get("text", "").strip()
                        process_message(chat_id, text)
                        time.sleep(1)
                        
        except Exception as e:
            if signals_object:
                signals_object.log_signal.emit(f"⚠️ خطای ربات: {e}")
                signals_object.status_signal.emit(False)
            time.sleep(5)
