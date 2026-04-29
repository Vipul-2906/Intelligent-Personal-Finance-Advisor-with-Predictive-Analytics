"""
ml/train_models.py
------------------
Generates synthetic finance dataset, engineers features,
trains classification & regression models, and saves the best ones.

Run:  python ml/train_models.py
"""

import os
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import accuracy_score, mean_squared_error
from xgboost import XGBClassifier

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

# ── 1. Synthetic Dataset ──────────────────────────────────────────────────────
def generate_dataset(n=2000):
    income = np.random.randint(25000, 150000, n)
    rent = income * np.random.uniform(0.20, 0.40, n)
    food = income * np.random.uniform(0.08, 0.20, n)
    transport = income * np.random.uniform(0.03, 0.10, n)
    entertainment = income * np.random.uniform(0.02, 0.15, n)
    healthcare = income * np.random.uniform(0.01, 0.06, n)

    total_expense = rent + food + transport + entertainment + healthcare
    # Savings derived from income minus expenses — realistic, not independent
    savings = np.maximum(0, income - total_expense) * np.random.uniform(0.50, 1.0, n)

    budget_goal = income * np.random.uniform(0.55, 0.85, n)
    goal_achieved = (total_expense <= budget_goal).astype(int)
    noise = np.random.normal(0, 2000, n)
    next_month_expense = total_expense * np.random.uniform(0.92, 1.10, n) + noise
    next_month_expense = np.clip(next_month_expense, 5000, None)

    df = pd.DataFrame({
        'monthly_income': income,
        'rent': rent,
        'food': food,
        'transport': transport,
        'entertainment': entertainment,
        'healthcare': healthcare,
        'savings': savings,
        'total_expense': total_expense,
        'budget_goal': budget_goal,
        'goal_achieved': goal_achieved,
        'next_month_expense': next_month_expense,
    })
    return df

# ── 2. Feature Engineering ────────────────────────────────────────────────────
def engineer_features(df):
    df = df.copy()
    df['savings_rate']       = df['savings'] / df['monthly_income']
    df['expense_ratio']      = df['total_expense'] / df['monthly_income']
    df['discretionary_ratio']= df['entertainment'] / df['monthly_income']
    df['rent_ratio']         = df['rent'] / df['monthly_income']
    df['food_ratio']         = df['food'] / df['monthly_income']
    return df

FEATURE_COLS = [
    'monthly_income', 'total_expense', 'savings',
    'savings_rate', 'expense_ratio', 'discretionary_ratio',
    'rent_ratio', 'food_ratio',
]

# ── 3. Train Classification ───────────────────────────────────────────────────
def train_classification(df):
    X = df[FEATURE_COLS]
    y = df['goal_achieved']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_STATE)

    models = {
        'logistic': LogisticRegression(max_iter=500, random_state=RANDOM_STATE),
        'random_forest': RandomForestClassifier(n_estimators=150, random_state=RANDOM_STATE),
        # use_label_encoder removed in XGBoost >= 1.6
        'xgboost': XGBClassifier(n_estimators=150, eval_metric='logloss', random_state=RANDOM_STATE),
    }

    best_model, best_acc, best_name = None, 0, ''
    print("\n── Classification Results ──")
    for name, model in models.items():
        model.fit(X_train, y_train)
        acc = accuracy_score(y_test, model.predict(X_test))
        print(f"  {name:20s}: accuracy = {acc:.4f}")
        if acc > best_acc:
            best_acc, best_model, best_name = acc, model, name

    print(f"\n  ✅ Best classifier: {best_name} (accuracy={best_acc:.4f})")
    return best_model, FEATURE_COLS

# ── 4. Train Regression ───────────────────────────────────────────────────────
def train_regression(df):
    X = df[FEATURE_COLS]
    y = df['next_month_expense']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=RANDOM_STATE)

    models = {
        'random_forest': RandomForestRegressor(n_estimators=150, random_state=RANDOM_STATE),
        'gradient_boosting': GradientBoostingRegressor(n_estimators=150, random_state=RANDOM_STATE),
    }

    best_model, best_rmse, best_name = None, float('inf'), ''
    print("\n── Regression Results ──")
    for name, model in models.items():
        model.fit(X_train, y_train)
        # squared=False removed in sklearn >= 1.4; use sqrt(mse) instead
        mse = mean_squared_error(y_test, model.predict(X_test))
        rmse = mse ** 0.5
        print(f"  {name:20s}: RMSE = {rmse:.2f}")
        if rmse < best_rmse:
            best_rmse, best_model, best_name = rmse, model, name

    print(f"\n  ✅ Best regressor: {best_name} (RMSE={best_rmse:.2f})")
    return best_model, FEATURE_COLS

# ── 5. Save Models ────────────────────────────────────────────────────────────
def save_model(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(obj, f)
    print(f"  Saved → {path}")

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("Generating dataset …")
    df = generate_dataset(2000)
    df = engineer_features(df)
    print(f"  Dataset shape: {df.shape}")

    goal_model, goal_features   = train_classification(df)
    expense_model, exp_features = train_regression(df)

    print("\nSaving models …")
    save_model({'model': goal_model,    'features': goal_features},   'models/goal_model.pkl')
    save_model({'model': expense_model, 'features': exp_features},    'models/expense_model.pkl')
    print("\n🎉 Training complete.")
