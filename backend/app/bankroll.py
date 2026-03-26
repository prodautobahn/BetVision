# backend/app/bankroll.py
def flat_bet(stake_percentage=0.02, bankroll=1000):
    return round(stake_percentage * bankroll, 2)

def kelly_bet(odd, model_prob, bankroll, max_frac=0.05):
    b = odd - 1
    p = model_prob
    q = 1 - p
    kelly = (b * p - q) / b
    stake_frac = max(0.01, min(kelly, max_frac))
    return round(stake_frac * bankroll, 2)
