# 🏦 Intelligent Personal Finance Advisor PRO
### Predictive Analytics & AI Insights — Upgrade Guide

---

## 📁 Project Structure

```
FinancePRO_Upgraded/
├── app.py                  ← Main Flask backend (upgraded)
├── db_config.py            ← MySQL connection config
├── database.sql            ← Full schema with new tables
├── requirements.txt        ← Python dependencies
│
├── ml/
│   ├── __init__.py
│   └── train_models.py     ← Dataset generation + model training
│
├── models/                 ← Saved ML model files (auto-created)
│   ├── goal_model.pkl
│   └── expense_model.pkl
│
├── utils/
│   ├── __init__.py
│   ├── predictor.py        ← ML inference + Explainable AI
│   ├── insights.py         ← Rule-based insights + health score
│   └── chatbot.py          ← AI financial chatbot engine
│
├── templates/              ← All HTML pages
│   ├── index.html          ← Login / Signup
│   ├── dashboard.html      ← ✨ Upgraded: health score, insights
│   ├── budget.html
│   ├── transactions.html
│   ├── goals.html
│   ├── prediction.html     ← ✨ New: ML results + XAI + what-if
│   ├── emergency.html      ← ✨ New: Emergency fund module
│   └── chatbot.html        ← ✨ New: AI financial chatbot
│
└── static/
    ├── style.css
    └── script.js
```

---

## ⚡ Step-by-Step Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

> **MySQL system library required:**
> - Ubuntu/Debian: `sudo apt-get install libmysqlclient-dev`
> - macOS: `brew install mysql-client`

---

### 2. Configure MySQL

Edit `db_config.py` and set your credentials:

```python
app.config['MYSQL_HOST']     = 'localhost'
app.config['MYSQL_USER']     = 'root'
app.config['MYSQL_PASSWORD'] = 'YOUR_PASSWORD'
app.config['MYSQL_DB']       = 'finance_advisor'
```

Or set environment variables:

```bash
export MYSQL_PASSWORD=your_password
```

---

### 3. Create the Database

```bash
mysql -u root -p < database.sql
```

This creates the `finance_advisor` database with all tables including:
- `emergency_fund`
- `predictions`
- `chatbot_logs`

---

### 4. Train the ML Models

```bash
python ml/train_models.py
```

This will:
- Generate a 2,000-row synthetic finance dataset
- Engineer features (savings_rate, expense_ratio, discretionary_ratio, etc.)
- Train and compare multiple classifiers (Logistic Regression, Random Forest, XGBoost)
- Train and compare regression models (Random Forest, Gradient Boosting)
- Save the best models to `models/goal_model.pkl` and `models/expense_model.pkl`

Expected output:
```
── Classification Results ──
  logistic            : accuracy = 0.82xx
  random_forest       : accuracy = 0.90xx
  xgboost             : accuracy = 0.91xx

  ✅ Best classifier: xgboost (accuracy=0.91xx)

── Regression Results ──
  random_forest       : RMSE = 1850.xx
  gradient_boosting   : RMSE = 1620.xx

  ✅ Best regressor: gradient_boosting (RMSE=1620.xx)
```

---

### 5. Run the Flask Backend

```bash
python app.py
```

Server starts at: `http://localhost:5000`

---

### 6. Open the Frontend

Serve the `templates/` folder with any static server:

```bash
# Option A — Python simple server (from the project root)
cd templates
python -m http.server 8080
# Visit: http://localhost:8080/index.html

# Option B — VS Code Live Server extension
# Right-click dashboard.html → Open with Live Server

# Option C — Deploy templates/ to any static host (Netlify, Vercel, etc.)
```

---

## 🔌 New API Endpoints

| Method | Endpoint              | Description                              |
|--------|-----------------------|------------------------------------------|
| GET    | `/emergency_status`   | Emergency fund status + risk level       |
| POST   | `/update_emergency_fund` | Add money to emergency fund           |
| POST   | `/predict_goal`       | ML goal achievement prediction           |
| POST   | `/predict_expense`    | ML next-month expense forecast           |
| POST   | `/explain_prediction` | Full XAI explanation + feature importance|
| GET    | `/insights`           | Smart insights + financial health score  |
| POST   | `/whatif`             | What-if scenario simulation              |
| POST   | `/chat`               | AI financial chatbot                     |
| GET    | `/dashboard_summary`  | Aggregated dashboard data                |

---

## 🤖 New Features Summary

### 1. Emergency Fund Module (`emergency.html`)
- Tracks 6-month expense target
- Progress bar with risk levels: 🔴 High / 🟡 Medium / 🟢 Safe
- One-click "Add Savings" to build the fund

### 2. Machine Learning System
- **Classification:** Predicts whether you'll achieve your budget goal
- **Regression:** Forecasts next month's total expenses
- Best model auto-selected based on accuracy (classification) and RMSE (regression)

### 3. Explainable AI (`prediction.html`)
- Shows WHY the model made each prediction
- Feature importance bar chart
- Human-readable reasoning (e.g., "Expense ratio is high at 0.85")

### 4. Smart Insights Engine
- Real-time rule-based alerts (overspending, low savings, rent too high, etc.)
- Personalised savings tips with exact rupee amounts

### 5. Financial Health Score
- 0–100 composite score based on savings rate, expense ratio, and emergency fund
- Labels: Excellent / Good / Fair / Poor

### 6. AI Chatbot (`chatbot.html`)
- Natural language queries
- Uses live user financial data + ML predictions
- Handles: goal status, forecasts, savings tips, what-if, health score, full summary
- All chat logs stored in `chatbot_logs` table

### 7. What-If Analysis (`prediction.html`)
- Simulate reducing any spending category by any amount
- Instantly see: new savings, new goal prediction, new health score

### 8. Upgraded Dashboard (`dashboard.html`)
- Health score ring animation
- Top 3 AI insights panel
- Prediction summary panel
- Emergency fund mini widget

---

## 🗄️ New Database Tables

```sql
-- Emergency fund per user
emergency_fund (fund_id, user_id, current_savings, updated_at)

-- ML prediction logs
predictions (pred_id, user_id, month, predicted_expense,
             goal_achieved, confidence, explanation, created_at)

-- Chatbot conversation history
chatbot_logs (log_id, user_id, user_message, bot_response, created_at)
```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| `Models not trained yet` | Run `python ml/train_models.py` first |
| MySQL connection error | Check credentials in `db_config.py` |
| CORS error in browser | Ensure Flask is running on port 5000 |
| `ModuleNotFoundError: xgboost` | Run `pip install xgboost` |
| Import error for utils | Run `app.py` from the project root directory |

---

## 🚀 Production Deployment Notes

1. Replace `debug=True` with `debug=False` in `app.py`
2. Use environment variables for all secrets (MySQL password, etc.)
3. Serve frontend with Nginx or a CDN
4. Use `gunicorn app:app` instead of `flask run`
5. Add a cron job to retrain models monthly with real user data
6. Consider Redis for chatbot session caching at scale
