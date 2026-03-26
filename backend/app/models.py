# backend/models.py
import json
from datetime import datetime
from sqlalchemy import (Column, Integer, String, Float, DateTime, Text,
                        ForeignKey, Boolean)
from sqlalchemy.orm import relationship
from .database import Base

# ── Matches ───────────────────────────────────────────────────────────────────
class Match(Base):
    __tablename__ = "matches"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id      = Column(Integer, unique=True, index=True, nullable=False)
    league_id       = Column(Integer, nullable=False)
    league_name     = Column(String, nullable=False)
    home_team_id    = Column(Integer, nullable=False)
    home_team_name  = Column(String, nullable=False)
    away_team_id    = Column(Integer, nullable=False)
    away_team_name  = Column(String, nullable=False)
    kickoff_time    = Column(DateTime, nullable=False)
    status          = Column(String, nullable=False)  # NS, FT, 1H, 2H …
    home_score      = Column(Integer, default=0)
    away_score      = Column(Integer, default=0)
    last_updated    = Column(DateTime, default=datetime.utcnow)

    odds       = relationship("Odds", back_populates="match")
    predictions = relationship("Prediction", back_populates="match")

    def to_dict(self):
        return {
            "fixture": f"{self.home_team_name} vs {self.away_team_name}",
            "league": self.league_name,
            "date": self.kickoff_time.isoformat(),
            "status": self.status,
            "home": self.home_team_name,
            "away": self.away_team_name,
            "1": None, "X": None, "2": None,  # rellenar después con preds
            "ev_1": None, "ev_X": None, "ev_2": None,
        }

# ── Odds ───────────────────────────────────────────────────────────────────────
class Odds(Base):
    __tablename__ = "odds"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id    = Column(Integer, ForeignKey("matches.fixture_id"))
    bookmaker_id  = Column(Integer, nullable=False)
    bookmaker_name= Column(String, nullable=False)
    market_name   = Column(String, nullable=False)   # 1X2, over_2.5, etc.
    outcome       = Column(String, nullable=False)   # 1, X, 2, 3.0, 0, 1–0, etc.
    odd           = Column(Float, nullable=False)
    last_updated  = Column(DateTime, default=datetime.utcnow)

    match = relationship("Match", back_populates="odds")

# ── Predictions ───────────────────────────────────────────────────────────────
class Prediction(Base):
    __tablename__ = "predictions"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    fixture_id    = Column(Integer, ForeignKey("matches.fixture_id"))
    market_name   = Column(String, nullable=False)
    probabilities= Column(Text, nullable=False)  # JSON string
    created_at    = Column(DateTime, default=datetime.utcnow)

    match = relationship("Match", back_populates="predictions")

    def to_dict(self):
        return {
            "fixture": self.match.home_team_name + " vs " + self.match.away_team_name,
            "market": self.market_name,
            "probabilities": json.loads(self.probabilities)
        }

# ── Value bets ─────────────────────────────────────────────────────────────────
class ValueBet(Base):
    __tablename__ = "value_bets"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    odd_id       = Column(Integer, ForeignKey("odds.id"))
    ev           = Column(Float, nullable=False)
    recommended  = Column(Boolean, default=True)
    last_checked = Column(DateTime, default=datetime.utcnow)

    odd = relationship("Odds")

    def to_dict(self):
        return {
            "fixture": f"{self.odd.match.home_team_name} vs {self.odd.match.away_team_name}",
            "market": self.odd.market_name,
            "outcome": self.odd.outcome,
            "odd": self.odd.odd,
            "model_prob": json.loads(self.odd.match.predictions[0].probabilities).get(self.odd.outcome, 0),
            "ev": self.ev,
            "stake": None  # se rellena en la UI según bankroll
        }

# ── Combined bets ─────────────────────────────────────────────────────────────
class CombinedBet(Base):
    __tablename__ = "combined_bets"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    description   = Column(String, nullable=False)  # e.g. "1+Over 2.5"
    probability   = Column(Float, nullable=False)
    odds          = Column(Float, nullable=False)
    ev            = Column(Float, nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "description": self.description,
            "probability": self.probability,
            "odds": self.odds,
            "ev": self.ev,
            "stake": None  # rellenar en UI según bankroll
        }
