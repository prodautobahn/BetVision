# backend/app/main.py
from fastapi import FastAPI
from .database import Base, engine
from .models import Match, ValueBet, CombinedBet
from .ingestion import scheduler
import uvicorn

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Bet‑Vision 2026 API")

# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------
@app.get("/api/matches")
def get_matches():
    with get_session() as session:
        rows = session.query(Match).filter(
            Match.status.in_(["NS", "FT", "1H", "2H"])
        ).order_by(Match.kickoff_time).all()
        return [r.to_dict() for r in rows]

@app.get("/api/value_bets")
def get_value_bets():
    with get_session() as session:
        rows = session.query(ValueBet).join(Odds).all()
        return [r.to_dict() for r in rows]

@app.get("/api/combined_bets")
def get_combined_bets():
    with get_session() as session:
        rows = session.query(CombinedBet).all()
        return [r.to_dict() for r in rows]

# ------------------------------------------------------------------
# Scheduler
# ------------------------------------------------------------------
scheduler.start()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
