# Bale-Accounting-Bot
A Python &amp; PyQt5 desktop application for accounting automation, integrated with Bale messenger and SQL Server for real-time stock, invoice, and PDF statement management.
# 🤖 Bale Accounting & Stock Management Bot (PyQt5 + SQL Server)

A comprehensive Python-based desktop application integrated with the **Bale Messenger API** and **SQL Server**. This system automates daily accounting workflows, allows role-based access control, enables instant stock checks, invoice retrieval, and generates right-aligned Persian PDF financial statements on the fly.

---

## ✨ Features

*   **🖥️ Desktop Control Panel (PyQt5):** A dark-themed GUI to monitor bot status, view real-time operation logs, and run the service seamlessly in the system tray.
*   **🔐 Multi-Level Authentication:** Secure password-based access control supporting three distinct user roles (Normal, Warehouse, and Full Access).
*   **📦 Real-Time Stock & Inventory Check:** Instant search by product code or name, retrieving live inventory levels directly from SQL Server.
*   **📑 Invoice Management:** Flexible search for sales and purchase invoices by number, displaying line items, quantities, and totals.
*   **📄 Persian PDF Statement Generator:** Automatic generation of fully right-aligned, professionally formatted Persian PDF account balance reports using ReportLab.
*   **🌐 E-Commerce Price Syncing:** Built-in multi-threading to fetch and sync product prices and colors with Webzi web shop endpoints.

---

## 🛠️ Architecture & Tech Stack

*   **GUI Framework:** PyQt5 (Python)
*   **Messaging API:** Bale Messenger API (Telegram-compatible HTTP endpoints)
*   **Database:** SQL Server / PyODBC
*   **PDF Generation:** ReportLab + Arabic-Reshaper & PyBidi (RTL Persian Text Support)
*   **Concurrency:** Python `threading` & `ThreadPoolExecutor`

---

## 📁 Project Structure

```text
├── main.pyw              # GUI Entry point & System Tray manager
├── bot_handlers.py      # Core message loops & Callback query processors
├── services.py          # Business logic & menu routers
├── database.py          # SQL Server queries & procedures
├── pdf_generators.py    # ReportLab PDF creation scripts
├── session_manager.py   # Web session & cookie refresher
├── utils.py             # RTL formatting & helper functions
└── config.py            # Central configuration & environment variables
