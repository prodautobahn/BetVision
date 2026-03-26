# backend/app/ingestion.py
import asyncio
import httpx
import pytz
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .database import get_session
from .models import Match, Market, Odds
from .config import settings

API_FOOTBALL_URL = "https://api-football-v1.p.rapidapi.com/v3/"
SPORTMONKS_URL = "https://api.sportmonks.com/v3/football/"

headers_ff = {"x-rapidapi-host": "api-football-v1.p.rapidapi.com",
              "x-rapidapi-key": settings.api_football_key}
headers_sm = {"token": settings.sportmonks_key}

async def fetch_json(url, params=None, headers=None):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, params=params, headers=headers)
        r.raise_for_status()
        return r.json()

async def update_matches(session: Session):
    # 1. Get all fixtures of today + tomorrow (to get upcoming)
    now = datetime.now(pytz.timezone("Europe/Madrid"))
    start = now - timedelta(days=7)          # past week for back‑testing
    end = now + timedelta(days=1)

    fixtures = await fetch_json(
        f"{API_FOOTBALL_URL}fixtures",
        params={"dateFrom": start.strftime("%Y-%m-%d"),
                "dateTo": end.strftime("%Y-%m-%d")},
        headers=headers_ff
    )
    for f in fixtures["response"]:
        m = session.query(Match).filter_by(fixture_id=f["fixture"]["id"]).first()
        if not m:
            m = Match(fixture_id=f["fixture"]["id"],
                      league_id=f["league"]["id"],
                      league_name=f["league"]["name"],
                      home_team_id=f["teams"]["home"]["id"],
                      home_team_name=f["teams"]["home"]["team_name"],
                      away_team_id=f["teams"]["away"]["id"],
                      away_team_name=f["teams"]["away"]["team_name"],
                      kickoff_time=f["fixture"]["date"],
                      status=f["fixture"]["status"]["short"],
                      home_score=f["fixture"]["goals"]["home"],
                      away_score=f["fixture"]["goals"]["away"],
                      last_updated=datetime.utcnow())
            session.add(m)
        else:
            # update live fields
            m.status = f["fixture"]["status"]["short"]
            m.home_score = f["fixture"]["goals"]["home"]
            m.away_score = f["fixture"]["goals"]["away"]
            m.last_updated = datetime.utcnow()
    session.commit()

async def update_odds(session: Session):
    # For each upcoming fixture fetch odds from SportMonks
    fixtures = session.query(Match).filter(
        Match.status.in_(["NS", "NS+"])  # Not Started
    ).all()
    for m in fixtures:
        odds_res = await fetch_json(
            f"{SPORTMONKS_URL}odds/{m.fixture_id}",
            headers=headers_sm
        )
        for odd in odds_res["data"]["bookmakers"]:
            for market in odd["markets"]:
                # Market mapping (example: 'h2h' => '1X2')
                market_code = market["name"]
                for odd_value in market["values"]:
                    # Store or update
                    o = session.query(Odds).filter_by(
                        fixture_id=m.fixture_id,
                        bookmaker_id=odd["bookmaker"]["id"],
                        market_name=market_code,
                        outcome=odd_value["label"]
                    ).first()
                    if not o:
                        o = Odds(fixture_id=m.fixture_id,
                                 bookmaker_id=odd["bookmaker"]["id"],
                                 bookmaker_name=odd["bookmaker"]["name"],
                                 market_name=market_code,
                                 outcome=odd_value["label"],
                                 odd=odd_value["odds"],
                                 last_updated=datetime.utcnow())
                        session.add(o)
                    else:
                        o.odd = odd_value["odds"]
                        o.last_updated = datetime.utcnow()
    session.commit()

async def periodic_task():
    async with get_session() as session:
        await update_matches(session)
        await update_odds(session)

# Scheduler (APScheduler)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
scheduler = AsyncIOScheduler()
scheduler.add_job(periodic_task, 'interval', minutes=settings.update_interval_minutes)
scheduler.start()
