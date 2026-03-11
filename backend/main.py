from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List

import crud

app = FastAPI(title="Multi-Sports Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SPORTS = ["cricket", "football", "basketball", "volleyball", "kabaddi", "handball", "table_tennis", "hockey", "softball"]

def validate_sport(sport: str):
    if sport not in SPORTS:
        raise HTTPException(status_code=400, detail="Invalid sport")

@app.get("/api/{sport}/tournaments")
def get_tournaments(sport: str):
    validate_sport(sport)
    return crud.get_tournaments(sport)

@app.post("/api/{sport}/tournaments")
def create_tournament(sport: str, item: Dict[str, Any]):
    validate_sport(sport)
    return crud.add_tournament(sport, item)

@app.delete("/api/{sport}/tournaments/{tid}")
def delete_tournament(sport: str, tid: int):
    validate_sport(sport)
    return crud.delete_tournament(sport, tid)

@app.get("/api/{sport}/teams")
def get_teams(sport: str, tournament_id: int = None):
    validate_sport(sport)
    return crud.get_teams(sport, tournament_id)

@app.post("/api/{sport}/teams")
def create_team(sport: str, item: Dict[str, Any]):
    validate_sport(sport)
    return crud.add_team(sport, item)

@app.delete("/api/{sport}/teams/{tid}")
def delete_team(sport: str, tid: int):
    validate_sport(sport)
    return crud.delete_team(sport, tid)

@app.get("/api/{sport}/players")
def get_players(sport: str, team_id: int = None):
    validate_sport(sport)
    return crud.get_players(sport, team_id)

@app.post("/api/{sport}/players")
def create_player(sport: str, item: Dict[str, Any]):
    validate_sport(sport)
    return crud.add_player(sport, item)

@app.delete("/api/{sport}/players/{pid}")
def delete_player(sport: str, pid: int):
    validate_sport(sport)
    return crud.delete_player(sport, pid)

@app.get("/api/{sport}/matches")
def get_matches(sport: str, tournament_id: int = None):
    validate_sport(sport)
    return crud.get_matches(sport, tournament_id)

@app.post("/api/{sport}/matches")
def create_match(sport: str, item: Dict[str, Any]):
    validate_sport(sport)
    return crud.add_match(sport, item)

@app.delete("/api/{sport}/matches/{mid}")
def delete_match(sport: str, mid: int):
    validate_sport(sport)
    return crud.delete_match(sport, mid)

@app.get("/api/{sport}/scores")
def get_scores(sport: str, match_id: int = None):
    validate_sport(sport)
    return crud.get_scores(sport, match_id)

@app.post("/api/{sport}/scores")
def create_score(sport: str, item: Dict[str, Any]):
    validate_sport(sport)
    return crud.add_score(sport, item)

@app.get("/api/{sport}/stats")
def get_stats(sport: str, tournament_id: int = None):
    validate_sport(sport)
    return crud.get_stats(sport, tournament_id)

__all__ = ["app"]
