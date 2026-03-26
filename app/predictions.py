# backend/app/predictions.py
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from .database import get_session
from .models import Match, Odds, Prediction
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.calibration import CalibratedClassifierCV
from datetime import datetime, timedelta
from sklearn.metrics import log_loss

# ---------- Helper: Build a features dataframe ----------
def build_features(session: Session, recent_days: int = 30):
    # 1. Pull matches of the last N days
    cutoff = datetime.utcnow() - timedelta(days=recent_days)
    matches = session.query(Match).filter(
        Match.kickoff_time >= cutoff,
        Match.status == "FT"
    ).all()
    data = []
    for m in matches:
        # team stats (goals per game, home advantage, etc.)
        # simple example: avg goals for, avg goals against
        home_avg = session.query(Match).filter(
            Match.home_team_id == m.home_team_id,
            Match.status == "FT"
        ).with_entities(
            Match.home_score, Match.away_score
        ).all()
        # compute averages
        # ... (omitted for brevity)

        # build feature vector
        fv = {
            "home_team_id": m.home_team_id,
            "away_team_id": m.away_team_id,
            "home_avg_goals": home_avg_home,
            "away_avg_goals": away_avg_away,
            "home_recent_win_rate": home_win_rate,
            "away_recent_win_rate": away_win_rate,
            # ... more features (Elo, injuries, etc.)
        }
        # target: outcome (1: home, 0: draw, 2: away)
        if m.home_score > m.away_score:
            target = 1
        elif m.home_score == m.away_score:
            target = 0
        else:
            target = 2
        fv["target"] = target
        data.append(fv)
    df = pd.DataFrame(data)
    return df
