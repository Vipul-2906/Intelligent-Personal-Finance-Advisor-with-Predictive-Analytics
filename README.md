# 💰 Intelligent Personal Finance Advisor with Predictive Analytics

A **Flask + MySQL** based full-stack web application that helps users manage their personal finances through **budget tracking, goal setting, expense monitoring, and predictive analytics**.  
The system intelligently analyzes past transactions to forecast **future spending trends** and offers **insights for better financial planning**.

---

## 🚀 Features

- 🔐 **User Authentication** — Secure signup/login with bcrypt-hashed passwords.  
- 💵 **Expense & Income Management** — Add, view, and categorize all transactions.  
- 🎯 **Goal Tracking** — Set financial goals and monitor progress over time.  
- 📊 **Budget Control** — Define monthly budgets and get alerts when exceeding limits.  
- 🤖 **Predictive Analytics** — Forecast next month’s expenses using a simple analytical model.  
- 📈 **Interactive Dashboard** — Visual charts powered by Chart.js.  
- 💾 **Persistent Data Storage** — All user data stored in a MySQL relational database.

---

## 🏗️ System Architecture

```
Frontend (HTML, CSS, JS)
         ↓
Flask Backend (app.py)
         ↓
MySQL Database (Database.sql)
```

---

## 🧩 Tech Stack

| Layer | Technology |
|-------|-------------|
| **Frontend** | HTML5, CSS3, Vanilla JavaScript, Chart.js |
| **Backend** | Python (Flask Framework) |
| **Database** | MySQL |
| **Authentication** | bcrypt |
| **Styling** | CSS3 + Google Fonts (Poppins) |
| **Visualization** | Chart.js |
| **Hosting (optional)** | Render / Heroku / Railway |

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/yourusername/finance-advisor.git
cd finance-advisor
```

### 2️⃣ Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Setup Environment Variables
Create a `.env` file in the root directory with:
```
DB_HOST=localhost
DB_USER=root
DB_PASS=yourpassword
DB_NAME=finance_db
SECRET_KEY=replace-with-strong-key
FLASK_ENV=development
```

### 5️⃣ Initialize Database
Import `Database.sql` into MySQL to create required tables.

### 6️⃣ Run the Application
```bash
python app.py
```
App runs at: http://127.0.0.1:5000/

---

## 📁 Project Structure

```
DBMS PRO/
│
├── app.py               # Flask backend with all API routes
├── db_config.py         # MySQL database configuration
├── Database.sql         # Database schema
├── requirements.txt     # Project dependencies
│
├── index.html           # Login & Signup page
├── dashboard.html       # Main user dashboard
├── budget.html          # Monthly budget tracker
├── transactions.html    # Add & view transactions
├── goals.html           # Set financial goals
├── prediction.html      # Expense predictions
│
├── style.css            # App styling
├── main.js              # Frontend logic & API handling
└── README.md            # Project documentation
```

---

## 🔍 API Endpoints Overview

| Endpoint | Method | Description |
|-----------|--------|-------------|
| `/signup` | POST | Register a new user |
| `/login` | POST | Authenticate existing user |
| `/transactions` | GET/POST | Fetch or add user transactions |
| `/add_budget` | POST | Add a monthly budget |
| `/get_budget` | GET | Fetch monthly budget summary |
| `/goals` | GET/POST | Create or fetch goals |
| `/predictions` | GET | Return expense predictions |
| `/` | GET | Health/Home route |

---

## 📈 Predictive Model Explanation

The system uses a **simple linear model** based on recent spending trends:
- Calculates the average of the last 6 months’ expenses.
- Applies a small multiplier (e.g., 1.05) to predict the next month’s expenses.
- Displays result visually using Chart.js.

This can later be upgraded to ML-based forecasting (ARIMA / Prophet / LSTM).

---

## 🧠 Future Enhancements

- Integrate **machine learning models** for better prediction accuracy.  
- Add **email verification** and **password reset**.  
- Introduce **PDF/CSV export** for transaction reports.  
- Implement **budget alert notifications**.  
- Create **mobile-friendly responsive UI**.  

---

## 🛡️ Security Practices

- Passwords hashed using bcrypt.  
- Parameterized SQL queries to prevent injection.  
- Planned HTTPS enforcement for deployment.  
- Secure environment variables for DB credentials.  

---

## 🧾 License

This project is open-source and available under the **MIT License**.

---

## 👨‍💻 Author

- Vipul Kumar  
