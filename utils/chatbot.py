"""
utils/chatbot.py
----------------
Rule-based + ML-driven financial chatbot engine.
"""

import re
from utils.insights import generate_insights, financial_health_score


def _get_predictor():
    """Lazy-load predictor so missing model files don't crash the module import."""
    from utils.predictor import predict_goal, predict_expense
    return predict_goal, predict_expense


def _fmt(n):
    return f"₹{n:,.0f}"


class FinanceChatbot:
    """Context-aware financial chatbot."""

    def __init__(self, user_data: dict):
        """
        user_data keys:
          name, monthly_income, total_expense, savings,
          rent, food, transport, entertainment, healthcare,
          emergency_progress (0-1 float)
        """
        self.d = user_data
        self.income        = float(user_data.get('monthly_income', 0))
        self.expense       = float(user_data.get('total_expense', 0))
        self.savings       = float(user_data.get('savings', 0))
        self.rent          = float(user_data.get('rent', 0))
        self.food          = float(user_data.get('food', 0))
        self.transport     = float(user_data.get('transport', 0))
        self.entertainment = float(user_data.get('entertainment', 0))
        self.healthcare    = float(user_data.get('healthcare', 0))
        self.em_progress   = float(user_data.get('emergency_progress', 0))
        self.name          = user_data.get('name', 'there')

    # ── Public API ──────────────────────────────────────────────────────────
    def respond(self, message: str) -> str:
        msg = message.lower().strip()

        # Greetings
        if re.search(r'\b(hi|hello|hey|good morning|good evening)\b', msg):
            return (f"Hello {self.name}! 👋 I'm your AI Finance Advisor. "
                    "Ask me anything — goal achievement, expense forecast, savings tips, "
                    "emergency fund status, or financial health.")

        # Goal prediction
        if re.search(r'\b(goal|target|achieve|budget goal)\b', msg):
            return self._goal_response()

        # Expense prediction
        if re.search(r'\b(next month|future expense|predict|forecast|spend next)\b', msg):
            return self._expense_response()

        # Savings tips
        if re.search(r'\b(save more|saving tips|how to save|increase savings|save money)\b', msg):
            return self._savings_tips()

        # Health score
        if re.search(r'\b(health score|financial health|score|rating)\b', msg):
            return self._health_response()

        # Emergency fund
        if re.search(r'\b(emergency|fund|safety net|risk)\b', msg):
            return self._emergency_response()

        # Overspending
        if re.search(r'\b(overspend|too much|spending|cut|reduce|expenses)\b', msg):
            return self._spending_response()

        # Rent advice
        if re.search(r'\b(rent|housing)\b', msg):
            return self._rent_response()

        # Entertainment
        if re.search(r'\b(entertainment|leisure|fun|movies|dining)\b', msg):
            return self._entertainment_response()

        # What-if
        if re.search(r'\b(what if|if i reduce|if i cut|simulate|scenario)\b', msg):
            return self._whatif_response(msg)

        # Summary
        if re.search(r'\b(summary|overview|status|how am i doing|analyse|analyze)\b', msg):
            return self._summary_response()

        return ("I can help you with: goal predictions, expense forecasts, savings tips, "
                "financial health score, emergency fund, and spending analysis. "
                "Try asking 'Will I achieve my goal?' or 'How can I save more?'")

    # ── Response Builders ───────────────────────────────────────────────────
    def _goal_response(self):
        predict_goal, _ = _get_predictor()
        result = predict_goal(self.d)
        achieved = result['goal_achieved']
        conf     = result['confidence']
        reasons  = result['explanation']['reasons']

        status = "✅ likely achieve" if achieved else "⚠️ may NOT achieve"
        lines  = [f"Based on your current financials, you {status} your budget goal (confidence: {conf}%)."]
        if reasons:
            lines.append("Key reasons:")
            for r in reasons:
                lines.append(f"  • {r}")
        if not achieved:
            lines.append(f"\n💡 Tip: Reducing expenses by {_fmt(self.expense * 0.10)} could significantly improve your chances.")
        return '\n'.join(lines)

    def _expense_response(self):
        _, predict_expense = _get_predictor()
        result = predict_expense(self.d)
        pred   = result['next_month_expense']
        drivers= result['explanation']['drivers']

        lines = [f"📈 Predicted next month's expenses: {_fmt(pred)}"]
        if self.income > 0:
            pct = pred / self.income
            lines.append(f"  That's {pct:.0%} of your income.")
        if drivers:
            lines.append("Main drivers:")
            for d in drivers:
                lines.append(f"  • {d}")
        return '\n'.join(lines)

    def _savings_tips(self):
        tips = []
        if self.income > 0:
            if self.entertainment / self.income > 0.10:
                save = round((self.entertainment / self.income - 0.10) * self.income)
                tips.append(f"🎬 Cut entertainment spending by {_fmt(save)}/month (currently {self.entertainment/self.income:.0%} of income, aim for 10%).")
            if self.food / self.income > 0.15:
                save = round((self.food / self.income - 0.15) * self.income)
                tips.append(f"🍽️ Reduce food spending by {_fmt(save)}/month by meal-prepping and avoiding delivery apps.")
            if self.transport / self.income > 0.10:
                tips.append("🚇 Consider public transport or carpooling to reduce transport costs.")
        tips.append("📦 Apply the 50-30-20 rule: 50% needs, 30% wants, 20% savings.")
        tips.append("🏦 Set up an auto-transfer to savings on payday so you save before you spend.")
        tips.append(f"🎯 Current savings: {_fmt(self.savings)}/month. Target at least {_fmt(self.income * 0.20)}/month (20%).")
        return "💰 Here are personalised savings tips:\n" + '\n'.join(f"  {t}" for t in tips)

    def _health_response(self):
        sr  = self.savings / self.income if self.income else 0
        er  = self.expense / self.income if self.income else 0
        hs  = financial_health_score(sr, er, self.em_progress)
        return (f"🏆 Your Financial Health Score: {hs['score']}/100 — {hs['label']}\n"
                f"  • Savings rate:     {sr:.0%} (target ≥ 20%)\n"
                f"  • Expense ratio:    {er:.0%} (target ≤ 70%)\n"
                f"  • Emergency fund:   {self.em_progress:.0%} of target")

    def _emergency_response(self):
        pct = self.em_progress * 100
        if pct < 30:
            risk = "🔴 HIGH RISK"
            advice = "Start building your emergency fund immediately. Even ₹1,000/month helps."
        elif pct < 70:
            risk = "🟡 MEDIUM RISK"
            advice = "You're on the right track. Keep contributing consistently."
        else:
            risk = "🟢 SAFE"
            advice = "Excellent! Your emergency fund provides solid protection."
        return (f"🛡️ Emergency Fund Status: {risk}\n"
                f"  Progress: {pct:.1f}% of 6-month target\n"
                f"  {advice}")

    def _spending_response(self):
        if self.income <= 0:
            return "Please add income transactions so I can analyse your spending."
        er = self.expense / self.income
        if er > 0.80:
            excess = round(self.expense - self.income * 0.70)
            return (f"🚨 You're overspending — expenses are {er:.0%} of income.\n"
                    f"  You need to cut {_fmt(excess)}/month to reach a healthy 70% expense ratio.\n"
                    "  Top areas to review: entertainment, dining out, subscriptions.")
        return (f"👍 Your expense ratio is {er:.0%} — within manageable range.\n"
                "  Continue tracking and look for small wins in discretionary spending.")

    def _rent_response(self):
        if self.income <= 0:
            return "Add your income to get personalised rent advice."
        rr = self.rent / self.income
        if rr > 0.35:
            return (f"🏠 Rent is {rr:.0%} of your income — above the 30% guideline.\n"
                    "  Consider: negotiating rent, a roommate, or relocating slightly.")
        return f"🏠 Rent ratio is {rr:.0%} — within the healthy 30% guideline. ✅"

    def _entertainment_response(self):
        if self.income <= 0:
            return "Add income data for personalised advice."
        dr = self.entertainment / self.income
        if dr > 0.12:
            save = round((dr - 0.10) * self.income)
            return (f"🎬 Entertainment is {dr:.0%} of income. Cutting to 10% saves {_fmt(save)}/month.\n"
                    "  Try: cancel unused subscriptions, cook at home more, use free entertainment.")
        return f"🎬 Entertainment spending ({dr:.0%} of income) is within a healthy range. ✅"

    def _whatif_response(self, msg):
        # Extract number if present
        match = re.search(r'(\d[\d,]*)', msg)
        amount = float(match.group(1).replace(',', '')) if match else self.entertainment * 0.20

        new_expense  = max(0, self.expense - amount)
        new_savings  = self.savings + amount
        new_sr       = new_savings / self.income if self.income else 0
        new_er       = new_expense / self.income if self.income else 0

        new_data = {**self.d, 'total_expense': new_expense, 'savings': new_savings}
        predict_goal, predict_expense = _get_predictor()
        new_goal     = predict_goal(new_data)
        new_pred_exp = predict_expense(new_data)

        status = "✅ YES" if new_goal['goal_achieved'] else "⚠️ NO"
        return (f"🔮 What-If Analysis — Reducing spending by {_fmt(amount)}/month:\n"
                f"  • New monthly savings:     {_fmt(new_savings)}\n"
                f"  • New savings rate:        {new_sr:.0%}\n"
                f"  • New expense ratio:       {new_er:.0%}\n"
                f"  • Goal achievement:        {status} (confidence: {new_goal['confidence']}%)\n"
                f"  • Predicted next expense:  {_fmt(new_pred_exp['next_month_expense'])}")

    def _summary_response(self):
        sr = self.savings / self.income if self.income else 0
        er = self.expense / self.income if self.income else 0
        hs = financial_health_score(sr, er, self.em_progress)
        predict_goal, _ = _get_predictor()
        goal = predict_goal(self.d)
        return (f"📊 Financial Summary for {self.name}:\n"
                f"  • Monthly income:   {_fmt(self.income)}\n"
                f"  • Total expenses:   {_fmt(self.expense)} ({er:.0%} of income)\n"
                f"  • Savings:          {_fmt(self.savings)} ({sr:.0%} of income)\n"
                f"  • Health Score:     {hs['score']}/100 ({hs['label']})\n"
                f"  • Goal achievement: {'✅ On track' if goal['goal_achieved'] else '⚠️ At risk'}\n"
                f"  • Emergency fund:   {self.em_progress:.0%} of target")
