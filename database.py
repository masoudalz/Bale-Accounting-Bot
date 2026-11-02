# database.py
import pyodbc
import random
import re
from datetime import datetime
import jdatetime
from utils import gregorian_to_jalali, format_number, convert_to_persian
from config import DB_CONN, HISTORY_START_YEAR


def get_customer_name(cust_code):
    if not cust_code:
        return "نامشخص"
    try:
        conn = pyodbc.connect(DB_CONN)
        cursor = conn.cursor()
        cursor.execute("SELECT NAME FROM ACCOUNT WHERE CODE = ?", (cust_code,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] if result and result[0] else "نامشخص"
    except:
        return "نامشخص"


def get_invoice_summary(sale_num):
    try:
        conn = pyodbc.connect(DB_CONN)
        cursor = conn.cursor()
        cursor.execute("SELECT SALE_NUM, SALE_DATE, CUST_CODE FROM SALE WHERE SALE_NUM = ?", (sale_num,))
        sale = cursor.fetchone()
        if not sale:
            return None
        customer_name = get_customer_name(sale[2])
        cursor.execute("SELECT COUNT(*) as ITEMS_COUNT, SUM(PRICE) as TOTAL FROM SALE_ROW WHERE SALE_NUM = ?", (sale_num,))
        row = cursor.fetchone()
        items_count = row[0] if row[0] else 0
        total = float(row[1]) if row[1] else 0
        cursor.close()
        conn.close()
        return {
            'num': sale_num,
            'date': gregorian_to_jalali(sale[1])[:10],
            'customer': customer_name,
            'items_count': items_count,
            'total': total
        }
    except Exception as e:
        print(f"Error: {e}")
        return None


def get_invoice_details(sale_num):
    try:
        conn = pyodbc.connect(DB_CONN)
        cursor = conn.cursor()
        cursor.execute("SELECT SALE_NUM, SALE_DATE, CUST_CODE, CUST_TEL FROM SALE WHERE SALE_NUM = ?", (sale_num,))
        sale = cursor.fetchone()
        if not sale:
            return None
        customer_name = get_customer_name(sale[2])
        cursor.execute("""
            SELECT g.NAME, sr.AMOUNT, sr.UNIT_PRICE, sr.PRICE
            FROM SALE_ROW sr
            LEFT JOIN GOOD g ON sr.GOOD_CODE = g.CODE
            WHERE sr.SALE_NUM = ?
            ORDER BY sr.NDX
        """, (sale_num,))
        items = cursor.fetchall()
        cursor.close()
        conn.close()
        total_amount = 0
        items_list = []
        for item in items:
            qty = float(item[1]) if item[1] else 0
            price = float(item[3]) if item[3] else 0
            unit_price = float(item[2]) if item[2] else 0
            items_list.append({
                'name': item[0] if item[0] else 'نامشخص',
                'quantity': format_number(qty),
                'unit_price': format_number(unit_price),
                'total': format_number(price)
            })
            total_amount += price
        return {
            'num': format_number(sale[0]),
            'date': gregorian_to_jalali(sale[1]),
            'customer': customer_name,
            'phone': sale[3] if sale[3] else 'ندارد',
            'items': items_list,
            'total_amount': format_number(total_amount),
            'items_count': len(items_list)
        }
    except Exception as e:
        print(f"Error: {e}")
        return None


def get_today_invoices():
    try:
        conn = pyodbc.connect(DB_CONN)
        cursor = conn.cursor()
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        cursor.execute("SELECT SALE_NUM FROM SALE WHERE SALE_DATE >= ? AND SALE_DATE <= ? ORDER BY SALE_NUM ASC", 
                       (today_start, today_end))
        invoices = cursor.fetchall()
        cursor.close()
        conn.close()
        result = []
        for inv in invoices:
            summary = get_invoice_summary(inv[0])
            if summary:
                result.append(summary)
        return result
    except Exception as e:
        print(f"Error: {e}")
        return []


def search_products(search_text):
    if not search_text or search_text.strip() == "":
        return []
    try:
        conn = pyodbc.connect(DB_CONN)
        cursor = conn.cursor()
        
        search = f"%{search_text.strip()}%"
        
        cursor.execute("""
            SELECT 
                p.CODE,
                p.NAME,
                ISNULL(SUM(r.REM), 0) as STOCK
            FROM v_PRODUCTS p
            LEFT JOIN v_GCMainRem r ON p.CODE = r.PRODUCT_CODE AND r.INV_CODE = 2
            WHERE p.NAME LIKE ? OR p.CODE LIKE ?
            GROUP BY p.CODE, p.NAME
            ORDER BY p.CODE
        """, (search, search))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        products = []
        for row in results:
            products.append({
                'code': row[0],
                'name': row[1] if row[1] else 'نامشخص',
                'stock': int(float(row[2])) if row[2] else 0
            })
        return products
    except Exception as e:
        print(f"Search error: {e}")
        return []


def flexible_search_name(search_text):
    if not search_text or len(search_text.strip()) < 1:
        return []
    
    raw_search = search_text.strip()
    
    try:
        conn = pyodbc.connect(DB_CONN)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT CODE, NAME
            FROM ACCOUNT
            WHERE NAME = ?
            ORDER BY NAME
        """, (raw_search,))
        
        exact_results = cursor.fetchall()
        
        if exact_results:
            results = []
            for row in exact_results:
                results.append({'code': row[0], 'name': row[1]})
            cursor.close()
            conn.close()
            return results
        
        search_words = raw_search.split()
        
        if len(search_words) == 1:
            cursor.execute("""
                SELECT CODE, NAME
                FROM ACCOUNT
                WHERE NAME LIKE ?
                ORDER BY 
                    CASE 
                        WHEN NAME LIKE ? THEN 1
                        WHEN NAME LIKE ? THEN 2
                        ELSE 3
                    END,
                    NAME
            """, (f"%{raw_search}%", f"{raw_search}%", f"% {raw_search} %"))
            
            results = cursor.fetchall()
            
            if results:
                output = []
                seen = set()
                for row in results:
                    name = row[1]
                    if name not in seen:
                        seen.add(name)
                        output.append({'code': row[0], 'name': name})
                cursor.close()
                conn.close()
                return output[:50]
            
            cursor.close()
            conn.close()
            return []
        
        conditions = []
        params = []
        
        for word in search_words:
            conditions.append("NAME LIKE ?")
            params.append(f"%{word}%")
        
        query = f"""
            SELECT CODE, NAME
            FROM ACCOUNT
            WHERE {' AND '.join(conditions)}
            ORDER BY NAME
        """
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        if results:
            output = []
            seen = set()
            for row in results:
                name = row[1]
                if name not in seen:
                    seen.add(name)
                    output.append({'code': row[0], 'name': name})
            cursor.close()
            conn.close()
            return output[:50]
        
        cursor.close()
        conn.close()
        return []
        
    except Exception as e:
        print(f"Flexible search error: {e}")
        return []


def search_person_for_statement(search_text):
    return flexible_search_name(search_text)


def search_customer_by_name(search_text):
    return flexible_search_name(search_text)


def get_customer_statement_data(account_code, customer_name):
    conn = pyodbc.connect(DB_CONN)
    cursor = conn.cursor()
    today = jdatetime.date.today()
    year_start = jdatetime.date(HISTORY_START_YEAR, 1, 1)
    from_date = year_start.togregorian()
    to_date = today.togregorian()
    
    node_num = random.randint(1, 999999)
    from_date_str = from_date.strftime('%Y-%m-%d')
    to_date_str = to_date.strftime('%Y-%m-%d')
    
    try:
        cursor.execute(f"DELETE FROM CT_CUSTREC2 WHERE NODE_NUM = {node_num}")
        sql = f"""
        DECLARE @from_date datetime = '{from_date_str}'
        DECLARE @to_date datetime = '{to_date_str}'
        EXEC pr_cust_rec2 {node_num}, '{account_code}', @from_date, @to_date
        """
        cursor.execute(sql)
    except Exception as e:
        print(f"Procedure error: {e}")
        try:
            cursor.execute(f"DELETE FROM CT_CUSTREC2 WHERE NODE_NUM = {node_num}")
            cursor.execute("EXEC pr_cust_rec2 ?, ?, NULL, NULL", (node_num, account_code))
        except Exception as e2:
            cursor.close()
            conn.close()
            return None
    
    cursor.execute("""
        SELECT ITM_NUM, ITM_DATE, ITM_TYPE, ITM_DEBT, ITM_CRED, NOTES, MANUAL_NUM, ITM_NDX
        FROM CT_CUSTREC2
        WHERE NODE_NUM = ? AND ACC_CODE = ?
        ORDER BY ITM_DATE, ITM_NUM, ITM_NDX
    """, (node_num, account_code))
    rows = cursor.fetchall()
    
    if not rows:
        cursor.execute(f"DELETE FROM CT_CUSTREC2 WHERE NODE_NUM = {node_num}")
        conn.commit()
        cursor.close()
        conn.close()
        return None
    
    type_map = {
        'DF': 'دریافت وجه', 'DnM': 'دریافت نقدی', 'DbC': 'دریافت با کارت/چک', 'c': 'تسویه',
        'P': 'خرید', 'Vat1': 'مالیات', 'Vat2': 'مالیات', 'Tf': 'تخفیف',
        'd': 'بدهکاری عادی', 'S': 'فروش', 'PnM': 'پرداخت نقدی', 'PbC': 'پرداخت چکی',
        'PR': 'پیش‌فاکتور', 'RbcB': 'برگشت از چک', 'RbcS': 'برگشت از چک', 'Tk': 'تخفیف', 'I': 'مانده اولیه'
    }
    
    transactions = []
    total_debt = 0
    total_cred = 0
    running_balance = 0
    
    for idx, row in enumerate(rows, 1):
        original_debt = float(row[3]) if row[3] else 0
        original_cred = float(row[4]) if row[4] else 0
        
        if row[2] == 'RbcS':
            debt = original_cred
            cred = 0
        else:
            debt = original_debt
            cred = original_cred
        
        total_debt += debt
        total_cred += cred
        
        running_balance += debt
        running_balance -= cred
        
        itm_date = row[1]
        try:
            if itm_date:
                jalali = jdatetime.datetime.fromgregorian(datetime=itm_date)
                date_str = jalali.strftime('%Y/%m/%d')
            else:
                date_str = 'نامشخص'
        except:
            date_str = str(itm_date)[:10] if itm_date else 'نامشخص'
        
        itm_type = type_map.get(row[2], row[2])
        manual_num = row[6] if row[6] else ''
        notes = row[5] if row[5] else ''
        description = manual_num if manual_num else notes
        if len(description) > 35:
            description = description[:32] + "..."
        
        transactions.append({
            'row': idx, 
            'doc_num': row[0], 
            'date': date_str, 
            'type': itm_type,
            'debt': debt, 
            'cred': cred, 
            'description': description,
            'balance': running_balance
        })
    
    cursor.execute(f"DELETE FROM CT_CUSTREC2 WHERE NODE_NUM = {node_num}")
    conn.commit()
    cursor.close()
    conn.close()
    
    return {
        'customer_code': account_code, 
        'customer_name': customer_name, 
        'transactions': transactions,
        'total_debt': total_debt, 
        'total_cred': total_cred, 
        'final_balance': total_debt - total_cred,
        'from_date': year_start.strftime('%Y/%m/%d'), 
        'to_date': today.strftime('%Y/%m/%d')
    }


def get_invoice_by_number(sale_num):
    try:
        conn = pyodbc.connect(DB_CONN)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT SALE_NUM, SALE_DATE, CUST_CODE, CUST_TEL 
            FROM SALE 
            WHERE SALE_NUM = ?
        """, (sale_num,))
        
        sale = cursor.fetchone()
        
        if sale:
            customer_name = get_customer_name(sale[2]) if sale[2] else 'نامشخص'
            
            cursor.execute("""
                SELECT 
                    g.NAME as GOOD_NAME,
                    sr.AMOUNT,
                    sr.UNIT_PRICE,
                    sr.PRICE,
                    sr.GOOD_CODE
                FROM SALE_ROW sr
                LEFT JOIN GOOD g ON sr.GOOD_CODE = g.CODE
                WHERE sr.SALE_NUM = ?
                ORDER BY sr.NDX
            """, (sale[0],))
            
            items = cursor.fetchall()
            cursor.close()
            conn.close()
            
            items_list = []
            total_amount = 0
            for item in items:
                qty = float(item[1]) if item[1] else 0
                unit_price = float(item[2]) if item[2] else 0
                price = float(item[3]) if item[3] else 0
                
                items_list.append({
                    'code': item[4] if item[4] else '',
                    'name': item[0] if item[0] else 'نامشخص',
                    'quantity': qty,
                    'unit_price': unit_price,
                    'total': price
                })
                total_amount += price
            
            return {
                'num': sale[0],
                'date': gregorian_to_jalali(sale[1]),
                'customer': customer_name,
                'customer_code': sale[2] if sale[2] else '',
                'phone': sale[3] if sale[3] else 'ندارد',
                'items': items_list,
                'total_amount': total_amount,
                'items_count': len(items_list),
                'invoice_type': 'S',
                'is_purchase': False
            }
        
        cursor.execute("""
            SELECT ACC_CODE, ITM_TYPE, ITM_DATE, ITM_DEBT, ITM_CRED, NOTES, MANUAL_NUM
            FROM CT_CUSTREC2
            WHERE ITM_NUM = ?
            ORDER BY ITM_DATE DESC
        """, (sale_num,))
        
        ct_results = cursor.fetchall()
        
        if not ct_results:
            cursor.close()
            conn.close()
            return None
        
        ct_row = ct_results[0]
        invoice_type = ct_row[1]
        acc_code = ct_row[0]
        sale_date = ct_row[2] if ct_row[2] else datetime.now()
        
        total_amount = float(ct_row[4]) if ct_row[4] else 0
        if total_amount == 0:
            total_amount = float(ct_row[3]) if ct_row[3] else 0
        
        customer_name = get_customer_name(acc_code) if acc_code else 'نامشخص'
        
        items_list = []
        
        try:
            cursor.execute("""
                SELECT 
                    g.NAME as GOOD_NAME,
                    pr.AMOUNT,
                    pr.UNIT_PRICE,
                    pr.PRICE,
                    pr.GOOD_CODE
                FROM PURCH_ROW pr
                LEFT JOIN GOOD g ON pr.GOOD_CODE = g.CODE
                WHERE pr.PURCHASE_NUM = ?
                ORDER BY pr.NDX
            """, (sale_num,))
            
            purch_items = cursor.fetchall()
            
            if purch_items and len(purch_items) > 0:
                for item in purch_items:
                    qty = float(item[1]) if item[1] else 0
                    unit_price = float(item[2]) if item[2] else 0
                    price = float(item[3]) if item[3] else 0
                    
                    items_list.append({
                        'code': item[4] if item[4] else '',
                        'name': item[0] if item[0] else 'نامشخص',
                        'quantity': qty,
                        'unit_price': unit_price,
                        'total': price
                    })
            else:
                notes = ct_row[5] if ct_row[5] else ''
                manual_num = ct_row[6] if ct_row[6] else ''
                
                items_list.append({
                    'code': '',
                    'name': f'فاکتور خرید - {manual_num if manual_num else sale_num}',
                    'quantity': 1,
                    'unit_price': total_amount,
                    'total': total_amount
                })
                
                if notes and len(notes) > 0:
                    items_list.append({
                        'code': '',
                        'name': f'توضیحات: {notes[:100]}',
                        'quantity': 1,
                        'unit_price': 0,
                        'total': 0
                    })
                    
        except Exception as e:
            print(f"Error getting PURCH_ROW: {e}")
            items_list.append({
                'code': '',
                'name': f'فاکتور خرید - شماره {sale_num}',
                'quantity': 1,
                'unit_price': total_amount,
                'total': total_amount
            })
        
        cursor.close()
        conn.close()
        
        return {
            'num': sale_num,
            'date': gregorian_to_jalali(sale_date),
            'customer': customer_name,
            'customer_code': acc_code if acc_code else '',
            'phone': 'ندارد',
            'items': items_list,
            'total_amount': total_amount,
            'items_count': len(items_list),
            'invoice_type': 'P',
            'is_purchase': True
        }
        
    except Exception as e:
        print(f"Error in get_invoice_by_number: {e}")
        return None
