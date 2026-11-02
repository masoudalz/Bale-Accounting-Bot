# utils.py
import requests
import json
import re
import jdatetime
from datetime import datetime
import arabic_reshaper
from bidi.algorithm import get_display

requests.packages.urllib3.disable_warnings()


def reshape_persian_text(text):
    if not text:
        return ""
    try:
        reshaped = arabic_reshaper.reshape(str(text))
        bidi_text = get_display(reshaped)
        return bidi_text
    except:
        return str(text)


def format_number(num):
    if num is None:
        return "0"
    try:
        return f"{int(float(num)):,}"
    except:
        return str(num)


def format_price(price):
    if price is None:
        return "0"
    try:
        price_int = int(float(price))
        return f"{price_int:,}"
    except:
        return str(price)


def gregorian_to_jalali(date_value):
    if not date_value:
        return 'نامشخص'
    try:
        if isinstance(date_value, datetime):
            jalali = jdatetime.datetime.fromgregorian(datetime=date_value)
            return jalali.strftime('%Y/%m/%d')
    except:
        pass
    return str(date_value)[:10] if date_value else 'نامشخص'


def convert_to_persian(text):
    if not text:
        return text
    replacements = {
        'ي': 'ی', 'ى': 'ی', 'ئ': 'ی',
        'ك': 'ک', 'ة': 'ه', 'إ': 'ا', 'أ': 'ا', 'آ': 'ا', 'ؤ': 'و',
    }
    for arabic, persian in replacements.items():
        text = text.replace(arabic, persian)
    return text


def normalize_persian_text(text):
    if not text:
        return ""
    text = str(text)
    replacements = {
        'ي': 'ی', 'ى': 'ی', 'ئ': 'ی',
        'ك': 'ک', 'ة': 'ه', 'إ': 'ا', 'أ': 'ا', 'آ': 'ا', 'ؤ': 'و',
    }
    for arabic, persian in replacements.items():
        text = text.replace(arabic, persian)
    arabic_diacritics = re.compile(r'[ً-ٰٟ]')
    text = arabic_diacritics.sub('', text)
    all_whitespace = re.compile(r'[\s -‏ -  　﻿]+')
    text = all_whitespace.sub('', text)
    return text


def send_message(chat_id, text):
    from config import BASE_URL
    url = f"{BASE_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=data, verify=False, timeout=10)
    except Exception as e:
        print(f"Send error: {e}")


def send_message_with_buttons(chat_id, text, buttons):
    from config import BASE_URL
    url = f"{BASE_URL}/sendMessage"
    markup = {"inline_keyboard": buttons}
    data = {"chat_id": chat_id, "text": text, "reply_markup": json.dumps(markup)}
    try:
        requests.post(url, json=data, verify=False, timeout=10)
    except Exception as e:
        print(f"Send error: {e}")


def send_document(chat_id, file_path, caption=""):
    from config import BASE_URL
    url = f"{BASE_URL}/sendDocument"
    try:
        with open(file_path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': chat_id, 'caption': caption}
            requests.post(url, files=files, data=data, verify=False, timeout=30)
    except Exception as e:
        print(f"Send document error: {e}")


def answer_callback(callback_id):
    from config import BASE_URL
    url = f"{BASE_URL}/answerCallbackQuery"
    data = {"callback_query_id": callback_id}
    try:
        requests.post(url, json=data, verify=False, timeout=10)
    except:
        pass
