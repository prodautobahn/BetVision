# backend/app/combined_bets.py
from itertools import combinations
from .models import ValueBet, CombinedBet, Odds
from .database import get_session
from datetime import datetime

def generate_combinations(session, max_len=3):
    """
    Produce combinadas de 2 a max_len eventos con EV+.
    """
    # Seleccionamos las apuestas con EV > 0
    bets = session.query(ValueBet).filter(
        ValueBet.ev > 0,
        ValueBet.last_checked >= datetime.utcnow() - timedelta(hours=1)
    ).all()

    combos = []
    for r in range(2, max_len+1):
        for combo in combinations(bets, r):
            # Evitar correlaciones altas (misma partida)
            fixture_ids = {b.odd.fixture_id for b in combo}
            if len(fixture_ids) < r:
                continue
            # Probabilidad combinada = prod(p_i) * corr_factor
            prob_comb = np.prod([b.ev + 1 for b in combo])  # rough
            # Calculamos odds combinada (multiplicamos los odds)
            odds_comb = np.prod([b.odd.odd for b in combo])
            ev_comb = prob_comb * odds_comb - 1
            if ev_comb > 0:
                combo_desc = " + ".join([f"{b.odd.market_name}={b.odd.outcome}" for b in combo])
                combined = CombinedBet(description=combo_desc,
                                      probability=prob_comb,
                                      odds=odds_comb,
                                      ev=ev_comb,
                                      created_at=datetime.utcnow())
                session.add(combined)
                combos.append(combined)
    session.commit()
    return combos
