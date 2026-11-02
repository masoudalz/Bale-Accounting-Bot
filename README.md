# 🤖 Bale Accounting & Stock Management Bot (PyQt5 + SQL Server)

A comprehensive Python-based desktop application integrated with the **Bale Messenger API** and **SQL Server**. This system automates daily accounting workflows, allows role-based access control, enables instant stock checks, invoice retrieval, and generates right-aligned Persian PDF financial statements on the fly.

---

## ✨ Key Features

* **🖥️ Desktop Control Panel (PyQt5):** A dark-themed GUI to monitor bot status, view real-time operation logs, and run the service seamlessly in the system tray.
* **🔐 Multi-Level Authentication:** Secure password-based access control supporting three distinct user roles (Normal, Warehouse, and Full Access).
* **📦 Real-Time Stock & Inventory Check:** Instant search by product code or name, retrieving live inventory levels directly from SQL Server.
* **📑 Invoice Management:** Flexible search for sales and purchase invoices by number, displaying line items, quantities, and totals.
* **📄 Persian PDF Statement Generator:** Automatic generation of fully right-aligned, professionally formatted Persian PDF account balance reports using ReportLab.
* **🌐 E-Commerce Price Syncing:** Built-in multi-threading to fetch and sync product prices and colors with web shop endpoints.

---

## 🛠️ Architecture & Tech Stack

* **GUI Framework:** PyQt5 (Python)
* **Messaging API:** Bale Messenger API (Telegram-compatible HTTP endpoints)
* **Database:** SQL Server / PyODBC
* **PDF Generation:** ReportLab + Arabic-Reshaper & PyBidi (RTL Persian Text Support)
* **Concurrency:** Python `threading` & `ThreadPoolExecutor`

---

## 📁 Project Structure

```text
Bale-Accounting-Bot/
├── main.pyw              # GUI Entry point & System Tray manager
├── bot_handlers.py      # Core message loops & Callback query processors
├── services.py          # Business logic & menu routers
├── database.py          # SQL Server queries & procedures
├── pdf_generators.py    # ReportLab PDF creation scripts
├── session_manager.py   # Web session & cookie refresher
├── utils.py             # RTL formatting & helper functions
└── config.py            # Central configuration & environment variables
```

---

## 🚀 Getting Started & Installation

### Prerequisites

* Python 3.8 or higher installed on Windows.
* SQL Server ODBC Driver (`ODBC Driver 17 for SQL Server` or similar).
* Required Persian TTF fonts installed on Windows (e.g., *B Nazanin*, *Tahoma*).

### Step-by-Step Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/masoudalz/Bale-Accounting-Bot.git
   cd Bale-Accounting-Bot
   ```

2. **Install required Python packages:**
   ```bash
   pip install pyqt5 pyodbc reportlab requests jdatetime arabic-reshaper python-bidi
   ```

3. **Configure Environment Variables / Settings (`config.py`):**
   Open `config.py` and set your database connection details, bot token, and passwords:
   * `DB_CONN`: Your SQL Server connection string (Server IP, Database Name, User, Password).
   * `BOT_TOKEN`: Your Bale messenger bot token.
   * `PASSWORD_NORMAL`, `PASSWORD_FULL`, `PASSWORD_WAREHOUSE`: Set your authorization credentials.

4. **Run the Application:**
   ```bash
   python main.pyw
   ```

---

## 🔒 Security Notice

Please ensure that production database credentials, private API tokens, and secret admin passwords are **never** committed directly to version control. Always utilize environment variables or keep your actual credentials in an untracked `config.py` file.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/masoudalz/Bale-Accounting-Bot/issues).

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.