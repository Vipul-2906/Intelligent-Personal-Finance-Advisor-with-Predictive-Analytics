"""
app.py — Finance Advisor PRO (Upgraded)
"""

import os
import calendar
from datetime import datetime

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_mysqldb import MySQL
import MySQLdb.cursors
import bcrypt

from db_config import init_db

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
mysql = init_db(app)

# Lazy-load ML utilities so the app boots without models
def _get_predictor():
    from utils.predictor import predict_goal, predict_expense
    return predict_goal, predict_expense

def _get_insights():
    from utils.insights import generate_insights, financial_health_score
    return generate_insights, financial_health_score

def _get_chatbot():
    from utils.chatbot import FinanceChatbot
    return FinanceChatbot


# ── Helpers ───────────────────────────────────────────────────────────────────
def safe_fetchall(cursor_obj):
    rows = cursor_obj.fetchall()
    return rows if rows else []

def get_cursor():
    try:
        mysql.connection.ping(True)
    except Exception:
        pass
    return mysql.connection.cursor(MySQLdb.cursors.DictCursor)

def _user_finance_summary(user_id, cursor):
    """Returns aggregated finance data for a user (current month)."""
    now = datetime.now()
    month_year = now.strftime('%Y-%m')

    cursor.execute("""
        SELECT COALESCE(SUM(amount),0) AS total
        FROM transactions WHERE user_id=%s AND type='income'
        AND DATE_FORMAT(date,'%%Y-%%m')=%s
    """, (user_id, month_year))
    income = float((cursor.fetchone() or {}).get('total', 0))

    cursor.execute("""
        SELECT category, COALESCE(SUM(amount),0) AS total
        FROM transactions WHERE user_id=%s AND type='expense'
        AND DATE_FORMAT(date,'%%Y-%%m')=%s
        GROUP BY category
    """, (user_id, month_year))
    categories = {r['category'].lower(): float(r['total']) for r in (safe_fetchall(cursor))}

    total_expense = sum(categories.values())

    # savings = income - expenses (can be negative when overspending)
    savings = income - total_expense

    # Emergency fund progress
    cursor.execute("SELECT current_savings FROM emergency_fund WHERE user_id=%s", (user_id,))
    ef_row = cursor.fetchone()
    current_savings = float(ef_row['current_savings']) if ef_row else 0

    # Required = 6 * avg monthly expense (use current month as proxy)
    required_fund = total_expense * 6 if total_expense > 0 else 0
    em_progress = min(1.0, current_savings / max(required_fund, 1))

    return {
        'monthly_income': income,
        'total_expense': total_expense,
        'savings': savings,
        'rent': categories.get('rent', 0),
        'food': categories.get('food', 0),
        'transport': categories.get('transport', 0),
        'entertainment': categories.get('entertainment', 0),
        'healthcare': categories.get('healthcare', 0),
        'emergency_progress': em_progress,
        'required_fund': round(required_fund, 2),
        'current_ef_savings': current_savings,
    }


# ══════════════════════════════════════════════════════════════════════════════
# EXISTING ROUTES (unchanged)
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json() or {}
    name, email, password = data.get('name'), data.get('email'), data.get('password')
    if not all([name, email, password]):
        return jsonify({'status': 'error', 'message': 'All fields are required'}), 400
    c = get_cursor()
    c.execute("SELECT * FROM users WHERE email=%s", (email,))
    if c.fetchone():
        c.close()
        return jsonify({'status': 'error', 'message': 'Account already exists'}), 400
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode('utf-8')
    c.execute("INSERT INTO users (name, email, password_hash) VALUES (%s,%s,%s)", (name, email, hashed))
    mysql.connection.commit()
    c.close()
    return jsonify({'status': 'success', 'message': 'Account created successfully'}), 200


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email, password = data.get('email'), data.get('password')
    c = get_cursor()
    c.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = c.fetchone()
    c.close()
    if user and bcrypt.checkpw(password.encode(), user['password_hash'].encode('utf-8')):
        return jsonify({'status': 'success', 'user': {
            'id': user['user_id'], 'name': user['name'], 'email': user['email']
        }}), 200
    return jsonify({'status': 'error', 'message': 'Invalid email or password'}), 401


@app.route('/add_budget', methods=['POST'])
def add_budget():
    data = request.get_json() or {}
    user_id, amount = data.get('user_id'), data.get('amount')
    if not user_id or amount is None:
        return jsonify({'status': 'error', 'message': 'user_id and amount required'}), 400
    try:
        amount_val = float(amount)
    except Exception:
        return jsonify({'status': 'error', 'message': 'Invalid amount'}), 400
    month_year = datetime.now().strftime('%Y-%m')
    c = get_cursor()
    c.execute("SELECT * FROM budget WHERE user_id=%s AND month_year=%s", (user_id, month_year))
    existing = c.fetchone()
    if existing:
        c.execute("UPDATE budget SET amount=%s WHERE budget_id=%s", (amount_val, existing['budget_id']))
    else:
        c.execute("INSERT INTO budget (user_id, amount, month_year) VALUES (%s,%s,%s)", (user_id, amount_val, month_year))
    mysql.connection.commit()
    c.close()
    return jsonify({'status': 'success', 'message': 'Budget set'}), 200


@app.route('/get_budget', methods=['GET'])
def get_budget():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'user_id required'}), 400
    now = datetime.now()
    curr_my = now.strftime('%Y-%m')
    c = get_cursor()
    c.execute("SELECT amount FROM budget WHERE user_id=%s AND month_year=%s", (user_id, curr_my))
    row = c.fetchone()
    budget_amount = float(row['amount']) if row else 0.0
    c.execute("""
        SELECT COALESCE(SUM(amount),0) AS spent FROM transactions
        WHERE user_id=%s AND type='expense' AND DATE_FORMAT(date,'%%Y-%%m')=%s
    """, (user_id, curr_my))
    spent_row = c.fetchone()
    spent = float(spent_row['spent']) if spent_row else 0.0
    remaining = round(budget_amount - spent, 2)
    total_days = calendar.monthrange(now.year, now.month)[1]
    days_left = max(0, total_days - now.day)
    note = "No budget set." if budget_amount <= 0 else (
        "🚨 Over budget!" if remaining < 0 else
        "✅ You're managing well!" if remaining / budget_amount >= 0.40 else
        "⚠️ Getting close to the limit!"
    )
    # Previous 3 months: budget amount + actual spend per month
    c.execute("""
        SELECT b.month_year, b.amount,
               COALESCE((
                   SELECT SUM(t.amount) FROM transactions t
                   WHERE t.user_id=%s AND t.type='expense'
                   AND DATE_FORMAT(t.date,'%%Y-%%m')=b.month_year
               ), 0) AS spent
        FROM budget b
        WHERE b.user_id=%s AND b.month_year < %s
        ORDER BY b.month_year DESC LIMIT 3
    """, (user_id, user_id, curr_my))
    prev_rows = safe_fetchall(c)
    previous_months = [
        {'month_year': r['month_year'], 'amount': float(r['amount']), 'spent': float(r['spent'])}
        for r in prev_rows
    ]
    c.close()
    return jsonify({'status': 'success', 'current': {
        'month_year': curr_my, 'amount': budget_amount, 'spent': spent,
        'remaining': remaining, 'remaining_days': days_left, 'note': note
    }, 'previous': previous_months}), 200


@app.route('/transactions', methods=['GET', 'POST'])
def transactions():
    c = get_cursor()
    if request.method == 'GET':
        user_id = request.args.get('user_id')
        if not user_id:
            c.close()
            return jsonify({'status': 'error', 'message': 'user_id required'}), 400
        c.execute("""SELECT txn_id, user_id, category, amount, type, date, created_at
                     FROM transactions WHERE user_id=%s ORDER BY date DESC, created_at DESC""", (user_id,))
        rows = safe_fetchall(c)
        c.close()
        return jsonify({'status': 'success', 'transactions': rows}), 200

    data = request.get_json() or {}
    user_id, category, amount, txn_type, date = (
        data.get('user_id'), data.get('category'), data.get('amount'),
        data.get('type'), data.get('date')
    )
    if not all([user_id, category, amount, txn_type, date]):
        c.close()
        return jsonify({'status': 'error', 'message': 'All fields required'}), 400
    try:
        c.execute("INSERT INTO transactions (user_id, category, amount, type, date) VALUES (%s,%s,%s,%s,%s)",
                  (user_id, category, amount, txn_type, date))
        mysql.connection.commit()
    except Exception as e:
        mysql.connection.rollback()
        c.close()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    c.close()
    return jsonify({'status': 'success', 'message': 'Transaction added'}), 200


@app.route('/goals', methods=['GET', 'POST'])
def goals():
    c = get_cursor()
    if request.method == 'GET':
        user_id = request.args.get('user_id')
        if not user_id:
            c.close()
            return jsonify({'status': 'error', 'message': 'user_id required'}), 400
        c.execute("SELECT * FROM goals WHERE user_id=%s ORDER BY goal_id DESC", (user_id,))
        rows = safe_fetchall(c)
        c.close()
        return jsonify({'status': 'success', 'goals': rows}), 200

    data = request.get_json() or {}
    user_id, name, target, date, saved = (
        data.get('user_id'), data.get('name'), data.get('target'),
        data.get('date'), data.get('saved', 0)
    )
    if not all([user_id, name, target, date]):
        c.close()
        return jsonify({'status': 'error', 'message': 'All fields required'}), 400
    try:
        c.execute("INSERT INTO goals (user_id, name, target, saved, date, status) VALUES (%s,%s,%s,%s,%s,%s)",
                  (user_id, name, target, saved, date, 'in_progress'))
        mysql.connection.commit()
    except Exception as e:
        mysql.connection.rollback()
        c.close()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    c.close()
    return jsonify({'status': 'success', 'message': 'Goal added'}), 200


@app.route('/update_goal', methods=['POST'])
def update_goal():
    data = request.get_json() or {}
    goal_id = data.get('goal_id')
    if not goal_id:
        return jsonify({'status': 'error', 'message': 'goal_id required'}), 400
    c = get_cursor()
    c.execute("UPDATE goals SET name=%s, target=%s, date=%s WHERE goal_id=%s",
              (data.get('name'), data.get('target'), data.get('date'), goal_id))
    mysql.connection.commit()
    c.close()
    return jsonify({'status': 'success', 'message': 'Goal updated'}), 200


@app.route('/delete_goal', methods=['POST'])
def delete_goal():
    data = request.get_json() or {}
    goal_id = data.get('goal_id')
    if not goal_id:
        return jsonify({'status': 'error', 'message': 'goal_id required'}), 400
    c = get_cursor()
    try:
        c.execute("DELETE FROM goal_savings WHERE goal_id=%s", (goal_id,))
    except Exception:
        pass
    c.execute("DELETE FROM goals WHERE goal_id=%s", (goal_id,))
    mysql.connection.commit()
    c.close()
    return jsonify({'status': 'success', 'message': 'Goal deleted'}), 200


@app.route('/add_goal_money', methods=['POST'])
def add_goal_money():
    data = request.get_json() or {}
    user_id, goal_id, amount, date, note = (
        data.get('user_id'), data.get('goal_id'), data.get('amount'),
        data.get('date'), data.get('note', None)
    )
    if not all([user_id, goal_id, amount, date]):
        return jsonify({'status': 'error', 'message': 'user_id, goal_id, amount, date required'}), 400
    try:
        amount_val = float(amount)
    except Exception:
        return jsonify({'status': 'error', 'message': 'Invalid amount'}), 400
    c = get_cursor()
    c.execute("SELECT saved, target, user_id FROM goals WHERE goal_id=%s", (goal_id,))
    goal = c.fetchone()
    if not goal:
        c.close()
        return jsonify({'status': 'error', 'message': 'Goal not found'}), 404
    c.execute("INSERT INTO goal_savings (user_id, goal_id, amount, date, note) VALUES (%s,%s,%s,%s,%s)",
              (user_id, goal_id, amount_val, date, note))
    c.execute("UPDATE goals SET saved=saved+%s WHERE goal_id=%s", (amount_val, goal_id))
    c.execute("SELECT saved, target FROM goals WHERE goal_id=%s", (goal_id,))
    g = c.fetchone()
    if g and float(g['saved']) >= float(g['target']):
        c.execute("UPDATE goals SET status='completed' WHERE goal_id=%s", (goal_id,))
    mysql.connection.commit()
    c.close()
    return jsonify({'status': 'success', 'message': 'Amount added'}), 200


@app.route('/goal_money_history', methods=['GET'])
def goal_money_history():
    user_id, goal_id = request.args.get('user_id'), request.args.get('goal_id')
    if not all([user_id, goal_id]):
        return jsonify({'status': 'error', 'message': 'user_id and goal_id required'}), 400
    c = get_cursor()
    c.execute("""SELECT id, user_id, goal_id, amount, date, note, created_at
                 FROM goal_savings WHERE user_id=%s AND goal_id=%s
                 ORDER BY date DESC""", (user_id, goal_id))
    rows = safe_fetchall(c)
    c.close()
    return jsonify({'status': 'success', 'history': rows}), 200


# ══════════════════════════════════════════════════════════════════════════════
# NEW ROUTES
# ══════════════════════════════════════════════════════════════════════════════

# ── Emergency Fund ────────────────────────────────────────────────────────────
@app.route('/emergency_status', methods=['GET'])
def emergency_status():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'user_id required'}), 400
    c = get_cursor()
    summary = _user_finance_summary(user_id, c)
    c.close()

    req   = summary['required_fund']
    curr  = summary['current_ef_savings']
    prog  = summary['emergency_progress']

    if prog < 0.30:
        risk = 'High Risk'
        risk_color = '#ef4444'
    elif prog < 0.70:
        risk = 'Medium'
        risk_color = '#f59e0b'
    else:
        risk = 'Safe'
        risk_color = '#22c55e'

    return jsonify({
        'status': 'success',
        'required_fund': req,
        'current_savings': curr,
        'progress': round(prog * 100, 1),
        'risk': risk,
        'risk_color': risk_color,
    }), 200


@app.route('/update_emergency_fund', methods=['POST'])
def update_emergency_fund():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    amount  = data.get('amount')
    if not user_id or amount is None:
        return jsonify({'status': 'error', 'message': 'user_id and amount required'}), 400
    c = get_cursor()
    c.execute("""INSERT INTO emergency_fund (user_id, current_savings)
                 VALUES (%s, %s)
                 ON DUPLICATE KEY UPDATE current_savings=current_savings+%s""",
              (user_id, float(amount), float(amount)))
    mysql.connection.commit()
    c.close()
    return jsonify({'status': 'success', 'message': 'Emergency fund updated'}), 200


# ── ML Predictions ────────────────────────────────────────────────────────────
@app.route('/predict_goal', methods=['POST'])
def predict_goal_route():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'user_id required'}), 400
    try:
        predict_goal, _ = _get_predictor()
        c = get_cursor()
        summary = _user_finance_summary(user_id, c)
        c.close()
        result = predict_goal(summary)
        # log prediction
        try:
            _, predict_expense_fn = _get_predictor()
            exp_result = predict_expense_fn(summary)
            predicted_expense_val = exp_result.get('next_month_expense')
        except Exception:
            predicted_expense_val = None
        try:
            c2 = get_cursor()
            c2.execute("""INSERT INTO predictions (user_id, month, predicted_expense, goal_achieved, confidence, explanation)
                          VALUES (%s,%s,%s,%s,%s,%s)""",
                       (user_id, datetime.now().strftime('%Y-%m'),
                        predicted_expense_val,
                        result['goal_achieved'], result['confidence'],
                        str(result['explanation']['reasons'])))
            mysql.connection.commit()
            c2.close()
        except Exception:
            pass
        return jsonify({'status': 'success', **result}), 200
    except FileNotFoundError:
        return jsonify({'status': 'error', 'message': 'Models not trained yet. Run ml/train_models.py first.'}), 503
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/predict_expense', methods=['POST'])
def predict_expense_route():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'user_id required'}), 400
    try:
        _, predict_expense = _get_predictor()
        c = get_cursor()
        summary = _user_finance_summary(user_id, c)
        c.close()
        result = predict_expense(summary)
        return jsonify({'status': 'success', **result}), 200
    except FileNotFoundError:
        return jsonify({'status': 'error', 'message': 'Models not trained yet. Run ml/train_models.py first.'}), 503
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/explain_prediction', methods=['POST'])
def explain_prediction():
    """Returns detailed feature importance explanation."""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'user_id required'}), 400
    try:
        predict_goal, predict_expense = _get_predictor()
        c = get_cursor()
        summary = _user_finance_summary(user_id, c)
        c.close()
        goal_result    = predict_goal(summary)
        expense_result = predict_expense(summary)
        return jsonify({
            'status': 'success',
            'goal': goal_result,
            'expense': expense_result,
            'user_profile': {
                'expense_ratio':        round(summary['total_expense'] / summary['monthly_income'], 4) if summary['monthly_income'] else 0,
                'savings_rate':         round(summary['savings'] / summary['monthly_income'], 4) if summary['monthly_income'] else 0,
                'discretionary_ratio':  round(summary['entertainment'] / summary['monthly_income'], 4) if summary['monthly_income'] else 0,
                'emergency_progress':   round(summary['emergency_progress'], 4),
            }
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ── Insights + Health Score ───────────────────────────────────────────────────
@app.route('/insights', methods=['GET'])
def insights():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'user_id required'}), 400
    generate_insights, financial_health_score = _get_insights()
    c = get_cursor()
    summary = _user_finance_summary(user_id, c)
    c.close()

    ins = generate_insights(
        income=summary['monthly_income'],
        total_expense=summary['total_expense'],
        savings=summary['savings'],
        entertainment=summary['entertainment'],
        rent=summary['rent'],
        emergency_progress=summary['emergency_progress'],
    )
    sr = summary['savings'] / summary['monthly_income'] if summary['monthly_income'] else 0
    er = summary['total_expense'] / summary['monthly_income'] if summary['monthly_income'] else 0
    hs = financial_health_score(sr, er, summary['emergency_progress'])

    return jsonify({'status': 'success', 'insights': ins, 'health_score': hs}), 200


# ── What-If Analysis ──────────────────────────────────────────────────────────
@app.route('/whatif', methods=['POST'])
def whatif():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    reduce_by = float(data.get('reduce_by', 0))
    category  = data.get('category', 'general')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'user_id required'}), 400
    try:
        predict_goal, predict_expense = _get_predictor()
        _, financial_health_score = _get_insights()
        c = get_cursor()
        summary = _user_finance_summary(user_id, c)
        c.close()

        new_expense = max(0, summary['total_expense'] - reduce_by)
        new_savings = summary['savings'] + reduce_by
        modified    = {**summary, 'total_expense': new_expense, 'savings': new_savings}

        goal_res = predict_goal(modified)
        exp_res  = predict_expense(modified)

        new_sr = new_savings / summary['monthly_income'] if summary['monthly_income'] else 0
        new_er = new_expense / summary['monthly_income'] if summary['monthly_income'] else 0
        new_hs = financial_health_score(new_sr, new_er, summary['emergency_progress'])

        return jsonify({
            'status': 'success',
            'scenario': {
                'reduce_by': reduce_by,
                'category': category,
                'new_monthly_savings': round(new_savings, 2),
                'new_expense_ratio': round(new_er, 4),
                'new_savings_rate': round(new_sr, 4),
                'new_health_score': new_hs,
                'goal_prediction': goal_res,
                'predicted_next_expense': exp_res['next_month_expense'],
            }
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ── Chatbot ───────────────────────────────────────────────────────────────────
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    message = data.get('message', '').strip()
    if not user_id or not message:
        return jsonify({'status': 'error', 'message': 'user_id and message required'}), 400

    try:
        FinanceChatbot = _get_chatbot()
        c = get_cursor()
        summary = _user_finance_summary(user_id, c)
        # get user name
        c.execute("SELECT name FROM users WHERE user_id=%s", (user_id,))
        u = c.fetchone()
        summary['name'] = u['name'] if u else 'User'
        c.close()

        bot = FinanceChatbot(summary)
        response = bot.respond(message)

        # log
        try:
            c2 = get_cursor()
            c2.execute("INSERT INTO chatbot_logs (user_id, user_message, bot_response) VALUES (%s,%s,%s)",
                       (user_id, message, response))
            mysql.connection.commit()
            c2.close()
        except Exception:
            pass

        return jsonify({'status': 'success', 'response': response}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ── Dashboard Summary ─────────────────────────────────────────────────────────
@app.route('/dashboard_summary', methods=['GET'])
def dashboard_summary():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'user_id required'}), 400

    generate_insights, financial_health_score = _get_insights()
    c = get_cursor()
    summary = _user_finance_summary(user_id, c)

    # Active goals count
    c.execute("SELECT COUNT(*) AS cnt FROM goals WHERE user_id=%s AND status='in_progress'", (user_id,))
    active_goals = (c.fetchone() or {}).get('cnt', 0)

    # Budget alert
    now = datetime.now()
    month_year = now.strftime('%Y-%m')
    c.execute("SELECT amount FROM budget WHERE user_id=%s AND month_year=%s", (user_id, month_year))
    b = c.fetchone()
    budget_amount = float(b['amount']) if b else 0
    budget_exceeded = 1 if (budget_amount > 0 and summary['total_expense'] > budget_amount) else 0

    # Monthly expense history (chart data)
    c.execute("""
        SELECT DATE_FORMAT(date,'%%Y-%%m') AS month, SUM(amount) AS total
        FROM transactions WHERE user_id=%s AND type='expense'
        GROUP BY month ORDER BY month DESC LIMIT 6
    """, (user_id,))
    hist = list(reversed(safe_fetchall(c)))
    c.close()

    sr = summary['savings'] / summary['monthly_income'] if summary['monthly_income'] else 0
    er = summary['total_expense'] / summary['monthly_income'] if summary['monthly_income'] else 0
    hs = financial_health_score(sr, er, summary['emergency_progress'])

    ins = generate_insights(
        income=summary['monthly_income'],
        total_expense=summary['total_expense'],
        savings=summary['savings'],
        entertainment=summary['entertainment'],
        rent=summary['rent'],
        emergency_progress=summary['emergency_progress'],
    )

    return jsonify({
        'status': 'success',
        'summary': {
            'income': summary['monthly_income'],
            'expense': summary['total_expense'],
            'savings': summary['savings'],
        },
        'health_score': hs,
        'insights': ins[:3],  # top 3
        'active_goals': active_goals,
        'budget_exceeded': budget_exceeded,
        'expense_chart': {
            'labels': [r['month'] for r in hist],
            'data': [float(r['total']) for r in hist],
        }
    }), 200


# ── Legacy predictions route (kept for compatibility) ─────────────────────────
@app.route('/predictions', methods=['GET'])
def predictions():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'status': 'error', 'message': 'user_id required'}), 400
    c = get_cursor()
    c.execute("""
        SELECT DATE_FORMAT(date,'%%Y-%%m') AS month, SUM(amount) AS total
        FROM transactions WHERE user_id=%s AND type='expense'
        GROUP BY month ORDER BY month DESC LIMIT 6
    """, (user_id,))
    rows = list(reversed(safe_fetchall(c)))
    c.close()
    labels = [r['month'] for r in rows]
    actual = [int(r['total']) for r in rows]
    if not actual:
        return jsonify({'status': 'success', 'labels': [], 'actual': [], 'predicted': [], 'next_pred': 0}), 200
    # Weighted average giving more weight to recent months for next_pred
    n = len(actual)
    weights = list(range(1, n + 1))
    next_pred = int(round(sum(a * w for a, w in zip(actual, weights)) / sum(weights)))
    # Projected series: for each position use the weighted avg of prior points
    # so it tracks alongside actual without the off-by-one shift
    projected = []
    for i in range(n):
        if i == 0:
            projected.append(actual[0])
        else:
            w = list(range(1, i + 2))
            projected.append(int(round(sum(a * wt for a, wt in zip(actual[:i+1], w)) / sum(w))))
    return jsonify({'status': 'success', 'labels': labels, 'actual': actual,
                    'predicted': projected, 'next_pred': next_pred}), 200


@app.route('/')
@app.route('/index')
def home():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/transactions_page')
def transactions_page():
    return render_template('transactions.html')

@app.route('/goals_page')
def goals_page():
    return render_template('goals.html')

@app.route('/budget')
def budget_page():
    return render_template('budget.html')

@app.route('/prediction')
def prediction_page():
    return render_template('prediction.html')

@app.route('/emergency')
def emergency_page():
    return render_template('emergency.html')

@app.route('/chatbot')
def chatbot_page():
    return render_template('chatbot.html')


if __name__ == '__main__':
    app.run(debug=True)
