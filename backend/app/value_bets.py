# backend/app/value_bets.py
import math
from .models import Odds, Prediction, ValueBet
from .database import get_session
from datetime import datetime

def implied_prob(odd):
    return 1 / odd

def compute_ev(prob_model, odd):
    # EV per unit stake
    return prob_model * odd - 1

def detect_value_bets(session):
    # Iterate over all live odds
    odds_list = session.query(Odds).filter(
        Odds.last_updated >= datetime.utcnow() - timedelta(minutes=10)
    ).all()
    for odd in odds_list:
        # Get model prediction for this market
        pred = session.query(Prediction).filter_by(
            fixture_id=odd.fixture_id,
            market_name=odd.market_name
        ).first()
        if not pred:
            continue
        probs = eval(pred.probabilities)  # dict {outcome: prob}
        prob_model = probs.get(odd.outcome)
        if prob_model is None:
            continue
        ev = compute_ev(prob_model, odd.odd)
        if ev > 0:
            vb = session.query(ValueBet).filter_by(
                odd_id=odd.id
            ).first()
            if not vb:
                vb = ValueBet(odd_id=odd.id,
                              ev=ev,
                              recommended=True,
                              last_checked=datetime.utcnow())
                session.add(vb)
            else:
                vb.ev = ev
                vb.last_checked = datetime.utcnow()
    session.commit()
