"""
utils/insights.py
-----------------
Generates rule-based financial insights from user data.
"""


def generate_insights(income: float, total_expense: float, savings: float,
                      entertainment: float, rent: float,
                      emergency_progress: float) -> list:
    """
    Returns a list of insight dicts:
      { 'type': 'warning'|'success'|'info', 'message': str }
    """
    insights = []

    if income <= 0:
        return [{'type': 'info', 'message': 'Add income transactions to unlock insights.'}]

    expense_ratio       = total_expense / income
    savings_rate        = savings / income
    discretionary_ratio = entertainment / income
    rent_ratio          = rent / income

    # Overspending
    if expense_ratio > 0.90:
        insights.append({'type': 'warning',
            'message': f'🚨 Critical overspending: expenses are {expense_ratio:.0%} of income. Immediate action needed.'})
    elif expense_ratio > 0.80:
        insights.append({'type': 'warning',
            'message': f'⚠️ You are overspending — expenses exceed 80% of income ({expense_ratio:.0%}).'})

    # Savings
    if savings_rate < 0.10:
        insights.append({'type': 'warning',
            'message': f'💸 Savings rate is critically low ({savings_rate:.0%}). Try the 50-30-20 rule.'})
    elif savings_rate < 0.20:
        insights.append({'type': 'info',
            'message': f'📊 Savings rate ({savings_rate:.0%}) is below the recommended 20%. Small cuts help.'})
    else:
        insights.append({'type': 'success',
            'message': f'✅ Great savings rate ({savings_rate:.0%})! Keep building your wealth.'})

    # Rent
    if rent_ratio > 0.40:
        insights.append({'type': 'warning',
            'message': f'🏠 Rent is {rent_ratio:.0%} of income — well above the 30% guideline.'})

    # Discretionary
    if discretionary_ratio > 0.15:
        saving_potential = round((discretionary_ratio - 0.10) * income)
        insights.append({'type': 'info',
            'message': f'🎬 Entertainment spending is high. Cutting it to 10% could save ₹{saving_potential:,}/month.'})

    # Emergency fund
    if emergency_progress < 0.30:
        insights.append({'type': 'warning',
            'message': '🆘 Emergency fund is critically low (< 30%). Prioritise building it.'})
    elif emergency_progress < 0.70:
        insights.append({'type': 'info',
            'message': '🛡️ Emergency fund is growing (30–70%). Aim for 6 months of expenses.'})
    else:
        insights.append({'type': 'success',
            'message': '🏆 Emergency fund is healthy (> 70%). You have a solid financial safety net.'})

    return insights


def financial_health_score(savings_rate: float, expense_ratio: float,
                            emergency_progress: float) -> dict:
    """
    Returns a score 0–100 and a label.
    """
    score = 0
    # Savings rate: max 40 pts
    score += min(40, savings_rate * 200)
    # Expense ratio: max 40 pts (lower is better)
    score += max(0, 40 - expense_ratio * 50)
    # Emergency fund: max 20 pts
    score += min(20, emergency_progress * 20)

    score = round(min(100, max(0, score)))

    if score >= 75:
        label = 'Excellent'
        color = '#22c55e'
    elif score >= 55:
        label = 'Good'
        color = '#3b82f6'
    elif score >= 35:
        label = 'Fair'
        color = '#f59e0b'
    else:
        label = 'Poor'
        color = '#ef4444'

    return {'score': score, 'label': label, 'color': color}
