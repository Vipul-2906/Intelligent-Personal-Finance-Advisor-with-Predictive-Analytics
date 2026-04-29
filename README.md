# Intelligent Personal Finance Advisor

A smart personal finance management system that helps users track expenses, manage savings goals, and make better financial decisions using predictive analytics.

## Features

- User registration and secure login  
- Add and manage income / expenses  
- Budget planning and monthly tracking  
- Savings goal management  
- Emergency fund monitoring  
- Predict next month expenses using Machine Learning  
- Predict goal achievement chances  
- Financial health score dashboard  
- AI chatbot for finance-related queries  
- What-if analysis for spending decisions  

## Tech Stack

### Frontend
- HTML
- CSS
- JavaScript

### Backend
- Python
- Flask

### Database
- MySQL

### Machine Learning
- Scikit-learn
- XGBoost
- Pandas
- NumPy

## Setup Guide

### 1. Clone Repository

```bash
git clone <repository-url>
cd FinanceAdvisor
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Database

Update MySQL credentials in `db_config.py`

```python
MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "your_password"
MYSQL_DB = "finance_advisor"
```

### 4. Import Database

```bash
mysql -u root -p < database.sql
```

### 5. Train Machine Learning Models

```bash
python ml/train_models.py
```

### 6. Run Application

```bash
python app.py
```

Open in browser:

```text
http://localhost:5000
```

## Project Structure

```text
app.py
database.sql
templates/
static/
backend/
ml/
models/
utils/
```

## Future Improvements

- Mobile application version  
- Real bank API integration  
- Advanced analytics dashboard  
- Investment suggestions  

## Author

Vipul Kumar
