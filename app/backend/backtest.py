# backend/app/backtest.py
import pandas as pd
from datetime import datetime
from .database import get_session
from .models import Match, Odds, ValueBet

def simulate_backtest(session, start_date, end_date, strategy="flat"):
    """
    strategy: 'flat' | 'kelly'
    """
    bets = session.query(ValueBet).join(Odds).filter(
        Odds.fixture_id == Match.fixture_id,
        Match.kickoff_time >= start_date,
        Match.kickoff_time <= end_date
    ).all()

    bankroll = 1000.0  # arbitrary
    history = []

    for vb in bets:
        odd = vb.odd
        ev = vb.ev
        stake = 1.0
        if strategy == "kelly":
            # Kelly fraction = (bp - q) / b
            b = odd.odd - 1
            p = ev / odd.odd  # approximate model probability from ev
            kelly = (b * p - (1 - p)) / b
            stake = max(0.01, min(kelly, 0.05)) * bankroll  # limit to 5%

        # Determine outcome
        match = session.query(Match).filter_by(fixture_id=odd.fixture_id).first()
        outcome = determine_outcome(match, odd.market_name, odd.outcome)
        if outcome:
            bankroll += stake * (odd.odd - 1)
        else:
            bankroll -= stake

        history.append({
            "date": match.kickoff_time,
            "stake": stake,
            "odd": odd.odd,
            "ev": ev,
            "bankroll": bankroll
        })

    df = pd.DataFrame(history)
    df["drawdown"] = df["bankroll"].cummax() - df["bankroll"]
    roi = (bankroll - 1000) / 1000
    win_rate = len(df[df["bankroll"] > df["bankroll"].shift()]) / len(df)
    sharpe = df["bankroll"].pct_change().mean() / df["bankroll"].pct_change().std()

    return {
        "roi": roi,
        "drawdown": df["drawdown"].max(),
        "win_rate": win_rate,
        "sharpe": sharpe
    }
