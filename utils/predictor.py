"""
utils/predictor.py
------------------
Loads saved models and exposes predict + explain helpers.
"""

import os
import pickle
import numpy as np

_BASE = os.path.join(os.path.dirname(__file__), '..', 'models')
_goal_bundle    = None
_expense_bundle = None


def _load():
    global _goal_bundle, _expense_bundle
    if _goal_bundle is None:
        with open(os.path.join(_BASE, 'goal_model.pkl'), 'rb') as f:
            _goal_bundle = pickle.load(f)
    if _expense_bundle is None:
        with open(os.path.join(_BASE, 'expense_model.pkl'), 'rb') as f:
            _expense_bundle = pickle.load(f)


def _build_features(data: dict) -> np.ndarray:
    """Convert raw user dict to feature vector."""
    income        = float(data.get('monthly_income', 1))
    total_expense = float(data.get('total_expense', 0))
    savings       = float(data.get('savings', 0))
    rent          = float(data.get('rent', 0))
    food          = float(data.get('food', 0))
    entertainment = float(data.get('entertainment', 0))

    savings_rate        = savings / income if income else 0
    expense_ratio       = total_expense / income if income else 0
    discretionary_ratio = entertainment / income if income else 0
    rent_ratio          = rent / income if income else 0
    food_ratio          = food / income if income else 0

    return np.array([[
        income, total_expense, savings,
        savings_rate, expense_ratio, discretionary_ratio,
        rent_ratio, food_ratio,
    ]])


def _feature_names():
    return [
        'monthly_income', 'total_expense', 'savings',
        'savings_rate', 'expense_ratio', 'discretionary_ratio',
        'rent_ratio', 'food_ratio',
    ]


def predict_goal(data: dict) -> dict:
    """Returns goal achievement prediction with confidence + explanation."""
    _load()
    model    = _goal_bundle['model']
    X        = _build_features(data)
    pred     = int(model.predict(X)[0])
    prob     = model.predict_proba(X)[0]
    conf     = round(float(max(prob)) * 100, 1)

    explanation = _explain_goal(model, X, data)
    return {
        'goal_achieved': pred,
        'confidence': conf,
        'explanation': explanation,
    }


def predict_expense(data: dict) -> dict:
    """Returns next-month expense prediction + explanation."""
    _load()
    model  = _expense_bundle['model']
    X      = _build_features(data)
    pred   = round(float(model.predict(X)[0]), 2)

    explanation = _explain_expense(model, X, data)
    return {
        'next_month_expense': pred,
        'explanation': explanation,
    }


# ── Explainability ────────────────────────────────────────────────────────────
def _explain_goal(model, X, data):
    names   = _feature_names()
    reasons = []

    income        = float(data.get('monthly_income', 1))
    total_expense = float(data.get('total_expense', 0))
    savings       = float(data.get('savings', 0))
    entertainment = float(data.get('entertainment', 0))

    expense_ratio       = total_expense / income if income else 0
    savings_rate        = savings / income if income else 0
    discretionary_ratio = entertainment / income if income else 0

    if expense_ratio > 0.80:
        reasons.append(f"Expense ratio is very high ({expense_ratio:.2f}) — you're spending most of your income.")
    elif expense_ratio > 0.65:
        reasons.append(f"Expense ratio is elevated ({expense_ratio:.2f}) — leave more room for savings.")

    if savings_rate < 0.10:
        reasons.append(f"Savings rate is critically low ({savings_rate:.2f}) — aim for at least 20%.")
    elif savings_rate < 0.20:
        reasons.append(f"Savings rate is below recommended level ({savings_rate:.2f}).")

    if discretionary_ratio > 0.12:
        reasons.append(f"Discretionary spending (entertainment) is high ({discretionary_ratio:.2f} of income).")

    if not reasons:
        reasons.append("Your spending profile looks healthy — keep it up!")

    # Feature importances if available
    importances = {}
    if hasattr(model, 'feature_importances_'):
        for n, imp in zip(names, model.feature_importances_):
            importances[n] = round(float(imp), 4)

    return {'reasons': reasons, 'feature_importances': importances}


def _explain_expense(model, X, data):
    income        = float(data.get('monthly_income', 1))
    total_expense = float(data.get('total_expense', 0))
    expense_ratio = total_expense / income if income else 0
    names         = _feature_names()

    drivers = []
    if expense_ratio > 0.75:
        drivers.append("High overall spending is the primary driver of your predicted expense.")
    rent = float(data.get('rent', 0))
    if rent / income > 0.35:
        drivers.append(f"Rent is consuming {rent/income:.0%} of income — above the 30% guideline.")

    importances = {}
    if hasattr(model, 'feature_importances_'):
        for n, imp in zip(names, model.feature_importances_):
            importances[n] = round(float(imp), 4)

    return {'drivers': drivers, 'feature_importances': importances}
