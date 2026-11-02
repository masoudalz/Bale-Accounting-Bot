# services.py
import os
import time
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import send_message, send_message_with_buttons, send_document, format_number, format_price
from database import (get_invoice_details, get_today_invoices, search_products, 
                      get_customer_statement_data, search_customer_by_name, 
                      get_invoice_by_number)
from pdf_generators import generate_statement_pdf
from session_manager import get_product_price_from_site, refresh_cookies_manually


def send_main_menu(chat_id):
    buttons = [
        [{"text": "📦 موجودی", "callback_data": "search_stock"}],
        [{"text": "💰 صورتحساب", "callback_data": "search_statement"}],
        [{"text": "🔍 جستجوی فاکتور", "callback_data": "search_invoice"}]
    ]
    send_message_with_buttons(
        chat_id,
        "به ربات حسابداری خوش آمدید!

"
        "📦 موجودی - جستجوی کالا در انبار
"
        "💰 صورتحساب - مشاهده صورتحساب مشتریان
"
        "🔍 جستجوی فاکتور - جستجوی فاکتور بر اساس شماره",
        buttons
    )


def send_warehouse_menu(chat_id):
    buttons = [
        [{"text": "🧾 فاکتورهای امروز", "callback_data": "today_invoices"}],
        [{"text": "📦 موجودی", "callback_data": "search_stock"}]
    ]
    send_message_with_buttons(
        chat_id,
        "به ربات حسابداری خوش آمدید!

"
        "✨ سطح دسترسی: انبار ✨

"
        "🧾 فاکتورهای امروز - مشاهده فاکتورهای فروش امروز
"
        "📦 موجودی - جستجوی کالا در انبار
"
        "💰 صورتحساب - مشاهده صورتحساب مشتریان",
        buttons
    )


def send_full_menu(chat_id):
    buttons = [
        [{"text": "🧾 فاکتورهای امروز", "callback_data": "today_invoices"}],
        [{"text": "📦 موجودی", "callback_data": "search_stock"}],
        [{"text": "💰 صورتحساب", "callback_data": "search_statement"}],
        [{"text": "🔍 جستجوی فاکتور", "callback_data": "search_invoice"}]
    ]
    send_message_with_buttons(
        chat_id,
        "به ربات حسابداری خوش آمدید!

"
        "✨ سطح دسترسی: کامل ✨

"
        "🔍 جستجوی فاکتور - جستجوی فاکتور بر اساس شماره
"
        "🧾 فاکتورهای امروز - مشاهده فاکتورهای فروش امروز
"
        "📦 موجودی - جستجوی کالا در انبار
"
        "💰 صورتحساب - مشاهده صورتحساب مشتریان",
        buttons
    )


def send_main_menu_buttons(chat_id, text):
    buttons = [
        [{"text": "📦 موجودی", "callback_data": "search_stock"}],
        [{"text": "💰 صورتحساب", "callback_data": "search_statement"}],
        [{"text": "🔍 جستجوی فاکتور", "callback_data": "search_invoice"}]
    ]
    send_message_with_buttons(chat_id, text, buttons)


def send_warehouse_menu_buttons(chat_id, text):
    buttons = [
        [{"text": "🧾 فاکتورهای امروز", "callback_data": "today_invoices"}],
        [{"text": "📦 موجودی", "callback_data": "search_stock"}]
    ]
    send_message_with_buttons(chat_id, text, buttons)


def send_full_menu_buttons(chat_id, text):
    buttons = [
        [{"text": "🧾 فاکتورهای امروز", "callback_data": "today_invoices"}],
        [{"text": "📦 موجودی", "callback_data": "search_stock"}],
        [{"text": "💰 صورتحساب", "callback_data": "search_statement"}],
        [{"text": "🔍 جستجوی فاکتور", "callback_data": "search_invoice"}]
    ]
    send_message_with_buttons(chat_id, text, buttons)


def send_stock_results(chat_id, products, search_text, access_level="normal"):
    if not products:
        if access_level == "full":
            send_full_menu_buttons(chat_id, f"🔍 نتیجه جستجو برای: '{search_text}'\n❌ کالایی یافت نشد.")
        elif access_level == "warehouse":
            send_warehouse_menu_buttons(chat_id, f"🔍 نتیجه جستجو برای: '{search_text}'\n❌ کالایی یافت نشد.")
        else:
            send_main_menu_buttons(chat_id, f"🔍 نتیجه جستجو برای: '{search_text}'\n❌ کالایی یافت نشد.")
        return
    
    send_message(chat_id, "⏳ در حال دریافت اطلاعات...")
    
    site_info = {}
    use_fallback = False
    
    try:
        test_products = products[:3]
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_code = {
                executor.submit(get_product_price_from_site, product['code']): product['code']
                for product in test_products
            }
            
            for future in as_completed(future_to_code):
                code = future_to_code[future]
                try:
                    info = future.result(timeout=10)
                    if info and info != "timeout" and info != "connection_error":
                        site_info[code] = info
                except:
                    pass
        
        if not site_info:
            use_fallback = True
            
    except Exception as e:
        print(f"Error getting prices: {e}")
        use_fallback = True
    
    if use_fallback:
        message = f"🔍 نتیجه جستجو برای: '{search_text}'\n"
        message += f"📊 تعداد کالاهای یافت شده: {len(products)}\n"
        message += "⚠️ قیمت‌ها در حال حاضر در دسترس نیست.\n"
        message += "=" * 40 + "\n\n"

        for product in products:
            message += f"📦 کالا: {product['name']}\n"
            message += f"📋 کد کالا: {product['code']}\n"
            message += f"📊 موجودی: {format_number(product['stock'])} عدد\n"
            message += "=" * 40 + "\n\n"

        if access_level == "full":
            send_full_menu_buttons(chat_id, message)
        elif access_level == "warehouse":
            send_warehouse_menu_buttons(chat_id, message)
        else:
            send_main_menu_buttons(chat_id, message)
        return
    
    with ThreadPoolExecutor(max_workers=30) as executor:
        future_to_code = {
            executor.submit(get_product_price_from_site, product['code']): product['code']
            for product in products
        }
        
        for future in as_completed(future_to_code):
            code = future_to_code[future]
            try:
                info = future.result(timeout=15)
                if info and info != "timeout" and info != "connection_error":
                    site_info[code] = info
            except:
                pass
    
    filtered_products = []
    for product in products:
        code = product['code']
        if code in site_info:
            filtered_products.append(product)
    
    if not filtered_products:
        message = f"🔍 نتیجه جستجو برای: '{search_text}'\n"
        message += f"📊 تعداد کالاهای یافت شده: {len(products)}\n"
        message += "⚠️ هیچ قیمتی برای این کالاها یافت نشد.\n"
        message += "=" * 40 + "\n\n"

        for product in products:
            message += f"📦 کالا: {product['name']}\n"
            message += f"📋 کد کالا: {product['code']}\n"
            message += f"📊 موجودی: {format_number(product['stock'])} عدد\n"
            message += "=" * 40 + "\n\n"

        if access_level == "full":
            send_full_menu_buttons(chat_id, message)
        elif access_level == "warehouse":
            send_warehouse_menu_buttons(chat_id, message)
        else:
            send_main_menu_buttons(chat_id, message)
        return
    
    message = f"🔍 نتیجه جستجو برای: '{search_text}'\n"
    message += f"📊 تعداد کالاهای یافت شده در دیتابیس: {len(products)}\n"
    message += f"📊 تعداد کالاهای موجود در سایت: {len(filtered_products)}\n"
    message += "=" * 40 + "\n\n"
    
    for product in filtered_products:
        code = product['code']
        name = product['name']
        stock = product['stock']
        
        info = site_info.get(code)
        
        message += f"📦 کالا: {name}\n"
        message += f"📋 کد کالا: {code}\n"
        message += f"📊 موجودی: {format_number(stock)} عدد\n"
        
        if info:
            if info.get('color'):
                message += f"🎨 رنگ: {info['color']}\n"
            
            if info.get('has_discount') and info.get('price_discount'):
                message += f"💰 قیمت اصلی: {format_price(info['price_regular'])} تومان\n"
                message += f"💰 قیمت تخفیف خورده: {format_price(info['price_discount'])} تومان\n"
            else:
                message += f"💰 قیمت: {format_price(info['price_regular'])} تومان\n"
        
        message += "=" * 40 + "\n\n"
    
    if access_level == "full":
        send_full_menu_buttons(chat_id, message)
    elif access_level == "warehouse":
        send_warehouse_menu_buttons(chat_id, message)
    else:
        send_main_menu_buttons(chat_id, message)


def send_invoice_message(chat_id, invoice):
    items_text = ""
    for i, item in enumerate(invoice['items'], 1):
        items_text += f"\n   {i}. {item['name']}\n     تعداد: {item['quantity']} عدد\n     قیمت واحد: {item['unit_price']} ریال\n     جمع: {item['total']} ریال\n"
    
    message = f"\n🧾 فاکتور فروش\n{'─' * 40}\n\n📄 شماره فاکتور: {invoice['num']}\n📅 تاریخ: {invoice['date']}\n👤 مشتری: {invoice['customer']}\n📞 تلفن: {invoice['phone']}\n\n{'─' * 40}\n📦 اقلام فاکتور ({invoice['items_count']} قلم):\n{items_text}\n{'─' * 40}\n\n💰 جمع کل فاکتور: {invoice['total_amount']} ریال\n"
    send_message(chat_id, message)


def send_all_today_invoices(chat_id, access_level="full"):
    invoices = get_today_invoices()
    if not invoices:
        if access_level == "full":
            send_full_menu_buttons(chat_id, "امروز هیچ فاکتوری ثبت نشده است.\n\nبرای ادامه، یکی از گزینه‌ها را انتخاب کنید:")
        elif access_level == "warehouse":
            buttons = [
                [{"text": "🧾 فاکتورهای امروز", "callback_data": "today_invoices"}],
                [{"text": "📦 موجودی", "callback_data": "search_stock"}]
            ]
            send_message_with_buttons(chat_id, "امروز هیچ فاکتوری ثبت نشده است.\n\nبرای ادامه، یکی از گزینه‌ها را انتخاب کنید:", buttons)
        else:
            send_main_menu_buttons(chat_id, "امروز هیچ فاکتوری ثبت نشده است.")
        return
    
    total_sales = 0
    send_message(chat_id, f"📊 لیست فاکتورهای امروز\nتعداد کل: {len(invoices)} فاکتور\n{'=' * 40}")
    
    for inv in invoices:
        details = get_invoice_details(inv['num'])
        if details:
            send_invoice_message(chat_id, details)
            total_sales += int(inv['total'])
            time.sleep(0.5)
    
    if access_level == "full":
        send_full_menu_buttons(chat_id, f"{'=' * 40}\n💰 جمع کل فروش امروز: {format_number(total_sales)} ریال\n\nبرای ادامه، یکی از گزینه‌ها را انتخاب کنید:")
    elif access_level == "warehouse":
        buttons = [
            [{"text": "🧾 فاکتورهای امروز", "callback_data": "today_invoices"}],
            [{"text": "📦 موجودی", "callback_data": "search_stock"}]
        ]
        send_message_with_buttons(chat_id, f"{'=' * 40}\n💰 جمع کل فروش امروز: {format_number(total_sales)} ریال\n\nبرای ادامه، یکی از گزینه‌ها را انتخاب کنید:", buttons)
    else:
        send_main_menu_buttons(chat_id, f"{'=' * 40}\n💰 جمع کل فروش امروز: {format_number(total_sales)} ریال")


def send_statement_as_pdf(chat_id, account_code, account_name, access_level="normal"):
    data = get_customer_statement_data(account_code, account_name)
    if not data:
        if access_level == "full":
            send_full_menu_buttons(chat_id, f"❌ هیچ تراکنشی برای {account_name} یافت نشد.")
        elif access_level == "warehouse":
            send_warehouse_menu_buttons(chat_id, f"❌ هیچ تراکنشی برای {account_name} یافت نشد.")
        else:
            send_main_menu_buttons(chat_id, f"❌ هیچ تراکنشی برای {account_name} یافت نشد.")
        return
    
    try:
        pdf_path = generate_statement_pdf(account_code, account_name, data)
        if pdf_path and os.path.exists(pdf_path):
            caption = f"🧾 صورتحساب فایل PDF: {account_name}"
            send_document(chat_id, pdf_path, caption)
            if access_level == "full":
                send_full_menu_buttons(chat_id, "برای ادامه، یکی از گزینه‌های زیر را انتخاب کنید:")
            elif access_level == "warehouse":
                send_warehouse_menu_buttons(chat_id, "برای ادامه، یکی از گزینه‌های زیر را انتخاب کنید:")
            else:
                send_main_menu_buttons(chat_id, "برای ادامه، یکی از گزینه‌های زیر را انتخاب کنید:")
        else:
            if access_level == "full":
                send_full_menu_buttons(chat_id, f"❌ خطا در ایجاد فایل PDF برای {account_name}")
            elif access_level == "warehouse":
                send_warehouse_menu_buttons(chat_id, f"❌ خطا در ایجاد فایل PDF برای {account_name}")
            else:
                send_main_menu_buttons(chat_id, f"❌ خطا در ایجاد فایل PDF برای {account_name}")
    except Exception as e:
        if access_level == "full":
            send_full_menu_buttons(chat_id, f"❌ خطا در ایجاد PDF: {str(e)[:100]}")
        elif access_level == "warehouse":
            send_warehouse_menu_buttons(chat_id, f"❌ خطا در ایجاد PDF: {str(e)[:100]}")
        else:
            send_main_menu_buttons(chat_id, f"❌ خطا در ایجاد PDF: {str(e)[:100]}")


def send_invoice_search_result(chat_id, invoice):
    is_purchase = invoice.get('is_purchase', False)
    invoice_type = invoice.get('invoice_type', '')
    
    if is_purchase or invoice_type == 'P':
        type_text = "خرید"
        type_emoji = "📥"
        person_label = "تامین‌کننده"
    else:
        type_text = "فروش"
        type_emoji = "🛒"
        person_label = "مشتری"
    
    header = f"\n🧾 جزییات فاکتور {type_text}\n"
    header += "─" * 50 + "\n\n"
    header += f"{type_emoji} نوع فاکتور: {type_text}\n"
    header += f"📄 شماره فاکتور: {invoice['num']}\n"
    header += f"📅 تاریخ: {invoice['date']}\n"
    header += f"👤 {person_label}: {invoice['customer']}\n"
    header += f"🔑 کد {person_label}: {invoice['customer_code']}\n"
    header += f"📞 تلفن: {invoice['phone']}\n"
    
    items_text = ""
    if invoice['items'] and len(invoice['items']) > 0:
        items_text += f"\n{'─' * 50}\n"
        items_text += f"📦 اقلام فاکتور ({invoice['items_count']} قلم):\n\n"
        
        for i, item in enumerate(invoice['items'], 1):
            items_text += f"   {i}. {item['name']}\n"
            items_text += f"     کد کالا: {item['code']}\n"
            items_text += f"     تعداد: {format_number(item['quantity'])} عدد\n"
            items_text += f"     قیمت واحد: {format_number(item['unit_price'])} ریال\n"
            items_text += f"     جمع: {format_number(item['total'])} ریال\n"
            items_text += "\n"
    
    footer = f"{'─' * 50}\n"
    footer += f"💰 جمع کل فاکتور: {format_number(invoice['total_amount'])} ریال\n"
    footer += "─" * 50
    
    full_message = header + items_text + footer
    
    if len(full_message) <= 4000:
        send_message(chat_id, full_message)
        return
    
    items_list = invoice['items']
    mid_point = len(items_list) // 2
    
    first_half_items = ""
    for i, item in enumerate(items_list[:mid_point], 1):
        first_half_items += f"   {i}. {item['name']}\n"
        first_half_items += f"     کد کالا: {item['code']}\n"
        first_half_items += f"     تعداد: {format_number(item['quantity'])} عدد\n"
        first_half_items += f"     قیمت واحد: {format_number(item['unit_price'])} ریال\n"
        first_half_items += f"     جمع: {format_number(item['total'])} ریال\n"
        first_half_items += "\n"
    
    part1 = header
    part1 += f"\n{'─' * 50}\n"
    part1 += f"📦 اقلام فاکتور (بخش ۱ از ۲ - {mid_point} قلم):\n\n"
    part1 += first_half_items
    part1 += f"{'─' * 50}\n"
    part1 += f"⏳ ادامه اقلام در پیام بعدی...\n"
    part1 += "─" * 50
    
    second_half_items = ""
    for i, item in enumerate(items_list[mid_point:], mid_point + 1):
        second_half_items += f"   {i}. {item['name']}\n"
        second_half_items += f"     کد کالا: {item['code']}\n"
        second_half_items += f"     تعداد: {format_number(item['quantity'])} عدد\n"
        second_half_items += f"     قیمت واحد: {format_number(item['unit_price'])} ریال\n"
        second_half_items += f"     جمع: {format_number(item['total'])} ریال\n"
        second_half_items += "\n"
    
    part2 = f"\n📦 ادامه اقلام فاکتور (بخش ۲ از ۲ - {len(items_list) - mid_point} قلم):\n\n"
    part2 += second_half_items
    part2 += footer
    
    send_message(chat_id, part1)
    time.sleep(0.5)
    send_message(chat_id, part2)


def search_invoice_by_number(chat_id, sale_num, access_level="normal"):
    try:
        sale_num_int = int(sale_num)
    except ValueError:
        send_message(chat_id, "❌ لطفاً یک شماره فاکتور معتبر (عددی) وارد کنید.")
        if access_level == "full":
            send_full_menu_buttons(chat_id, "برای ادامه، یکی از گزینه‌ها را انتخاب کنید:")
        elif access_level == "warehouse":
            send_warehouse_menu_buttons(chat_id, "برای ادامه، یکی از گزینه‌ها را انتخاب کنید:")
        else:
            send_main_menu_buttons(chat_id, "برای ادامه، یکی از گزینه‌ها را انتخاب کنید:")
        return
    
    invoice = get_invoice_by_number(sale_num_int)
    
    if not invoice:
        send_message(chat_id, f"❌ فاکتوری با شماره {sale_num} یافت نشد.")
        if access_level == "full":
            send_full_menu_buttons(chat_id, "برای ادامه، یکی از گزینه‌ها را انتخاب کنید:")
        elif access_level == "warehouse":
            send_warehouse_menu_buttons(chat_id, "برای ادامه، یکی از گزینه‌ها را انتخاب کنید:")
        else:
            send_main_menu_buttons(chat_id, "برای ادامه، یکی از گزینه‌ها را انتخاب کنید:")
        return
    
    send_invoice_search_result(chat_id, invoice)
    
    if access_level == "full":
        send_full_menu_buttons(chat_id, "✅ جستجوی فاکتور کامل شد.\nبرای ادامه، یکی از گزینه‌ها را انتخاب کنید:")
    elif access_level == "warehouse":
        send_warehouse_menu_buttons(chat_id, "✅ جستجوی فاکتور کامل شد.")
    else:
        send_main_menu_buttons(chat_id, "✅ جستجوی فاکتور کامل شد.")
