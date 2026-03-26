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

# Poisson: λ_home = (home_avg_goals + away_avg_goals_against)/2
def poisson_predictions(home_lambda, away_lambda, max_goals=5):
    probs = []
    for h in range(max_goals+1):
        for a in range(max_goals+1):
            p = poisson_pmf(h, home_lambda) * poisson_pmf(a, away_lambda)
            probs.append(((h, a), p))
    return probs

def poisson_pmf(k, lam):
    return np.exp(-lam) * (lam**k) / np.math.factorial(k)

def train_classifiers(df: pd.DataFrame):
    X = df.drop(columns="target")
    y = df["target"]

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Logistic Regression
    lr = LogisticRegression(max_iter=1000)
    lr.fit(X_train, y_train)
    lr_pred = lr.predict_proba(X_val)

    # Random Forest
    rf = RandomForestClassifier(n_estimators=200, max_depth=12)
    rf.fit(X_train, y_train)
    rf_pred = rf.predict_proba(X_val)

    # XGBoost
    xgb = XGBClassifier(n_estimators=300, learning_rate=0.05)
    xgb.fit(X_train, y_train)
    xgb_pred = xgb.predict_proba(X_val)

    # Calibration (Isotonic)
    lr_cal = CalibratedClassifierCV(lr, cv='prefit', method='isotonic')
    lr_cal.fit(X_train, y_train)
    lr_pred_cal = lr_cal.predict_proba(X_val)

    # Save best model by log-loss
    models = {
        "lr": lr_cal,
        "rf": rf,
        "xgb": xgb
    }
    return models

def compute_market_probabilities(match, model):
    # Example: 1X2 from classification probabilities
    probs = model.predict_proba(match.to_features_vector())[0]
    prob_home, prob_draw, prob_away = probs
    return {
        "1": prob_home,
        "X": prob_draw,
        "2": prob_away
    }

def compute_over_under_probs(match, model, line=2.5):
    # Poisson: sum probabilities of total goals > line
    probs = model.predict_proba(match.to_features_vector())[0]
    # For simplicity, use logistic model to predict total goals
    total_goals_pred = probs.sum()
    over_prob = 1 - scipy.stats.poisson.cdf(line, total_goals_pred)
    return over_prob

def compute_exact_goals(match, model, scoreline=(1,0)):
    # Use Poisson to get probability of that exact score
    # λ values from features
    home_lambda = match.home_avg_goals
    away_lambda = match.away_avg_goals
    return poisson_pmf(scoreline[0], home_lambda) * poisson_pmf(scoreline[1], away_lambda)

def store_predictions(session: Session, match_id, market_name, probs: dict):
    pred = session.query(Prediction).filter_by(
        fixture_id=match_id,
        market_name=market_name
    ).first()
    if not pred:
        pred = Prediction(fixture_id=match_id,
                          market_name=market_name,
                          probabilities=str(probs),
                          created_at=datetime.utcnow())
        session.add(pred)
    else:
        pred.probabilities = str(probs)
        pred.created_at = datetime.utcnow()
    session.commit()
