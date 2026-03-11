import os
import pandas as pd
from datetime import datetime

def get_csv_path(sport: str, module: str) -> str:
    sport_prefix = "tt" if sport == "table_tennis" else sport
    
    paths_to_check = [
        os.path.join("..", "sports_dashboard", "data", f"{sport_prefix}_{module}.csv"),
        os.path.join("..", "sports_dashboard", "data", sport, f"{sport_prefix}_{module}.csv"),
        os.path.join("..", "sports_data", f"{sport_prefix}_{module}.csv"),
        os.path.join("..", "sports_data", sport, f"{sport_prefix}_{module}.csv"),
    ]
    for p in paths_to_check:
        if os.path.exists(p):
            return p
            
    default_dir = os.path.join("..", "sports_dashboard", "data")
    os.makedirs(default_dir, exist_ok=True)
    return os.path.join(default_dir, f"{sport_prefix}_{module}.csv")

import math
def clean_records(records):
    for row in records:
        for k, v in row.items():
            if isinstance(v, float) and math.isnan(v):
                row[k] = None
    return records

def load_csv(path: str, columns: list = None):
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            df.columns = df.columns.str.strip()
            if columns:
                for col in columns:
                    if col not in df.columns:
                        df[col] = None
            return df
        except pd.errors.EmptyDataError:
            pass
    return pd.DataFrame(columns=columns) if columns else pd.DataFrame()

def save_csv(df: pd.DataFrame, path: str):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    df.to_csv(path, index=False)

def get_next_id(df: pd.DataFrame, id_col: str):
    if df.empty or id_col not in df.columns:
        return 1
    valid_ids = pd.to_numeric(df[id_col], errors='coerce').dropna()
    if valid_ids.empty:
        return 1
    return int(valid_ids.max()) + 1

def get_tournaments(sport: str):
    path = get_csv_path(sport, "tournaments")
    df = load_csv(path, ["tournament_id","tournament_name","start_date","end_date","location"])
    return clean_records(df.to_dict(orient="records"))

def add_tournament(sport: str, data: dict):
    path = get_csv_path(sport, "tournaments")
    df = load_csv(path, ["tournament_id","tournament_name","start_date","end_date","location"])
    new_id = get_next_id(df, "tournament_id")
    new_row = {"tournament_id": new_id, **data}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_csv(df, path)
    return new_row

def update_tournament(sport: str, tournament_id: int, data: dict):
    path = get_csv_path(sport, "tournaments")
    df = load_csv(path, ["tournament_id","tournament_name","start_date","end_date","location"])
    df['tournament_id'] = pd.to_numeric(df['tournament_id'], errors='coerce')
    idx = df.index[df['tournament_id'] == tournament_id].tolist()
    if not idx: return None
    for k, v in data.items(): df.at[idx[0], k] = v
    save_csv(df, path)
    return df.iloc[idx[0]].where(pd.notnull(df.iloc[idx[0]]), None).to_dict()

def delete_tournament(sport: str, tournament_id: int):
    path = get_csv_path(sport, "tournaments")
    df = load_csv(path)
    if "tournament_id" in df.columns:
        df['tournament_id'] = pd.to_numeric(df['tournament_id'], errors='coerce')
        df = df[df['tournament_id'] != tournament_id]
        save_csv(df, path)
    return {"status": "deleted"}

def get_teams(sport: str, tournament_id: int = None):
    path = get_csv_path(sport, "teams")
    df = load_csv(path, ["team_id", "team_name", "tournament_id"])
    if tournament_id is not None and not df.empty and "tournament_id" in df.columns:
        df['tournament_id'] = pd.to_numeric(df['tournament_id'], errors='coerce')
        df = df[df["tournament_id"] == tournament_id]
    return clean_records(df.to_dict(orient="records"))

def add_team(sport: str, data: dict):
    path = get_csv_path(sport, "teams")
    df = load_csv(path, ["team_id", "team_name", "tournament_id"])
    new_id = get_next_id(df, "team_id")
    new_row = {"team_id": new_id, **data}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_csv(df, path)
    return new_row

def delete_team(sport: str, team_id: int):
    path = get_csv_path(sport, "teams")
    df = load_csv(path)
    if "team_id" in df.columns:
        df['team_id'] = pd.to_numeric(df['team_id'], errors='coerce')
        df = df[df['team_id'] != team_id]
        save_csv(df, path)
    return {"status": "deleted"}

def get_players(sport: str, team_id: int = None):
    path = get_csv_path(sport, "players")
    df = load_csv(path, ["player_id", "player_name", "team_id", "phone_number", "profile_image"])
    if team_id is not None and not df.empty and "team_id" in df.columns:
        df['team_id'] = pd.to_numeric(df['team_id'], errors='coerce')
        df = df[df["team_id"] == team_id]
    return clean_records(df.to_dict(orient="records"))

def add_player(sport: str, data: dict):
    path = get_csv_path(sport, "players")
    df = load_csv(path, ["player_id", "player_name", "team_id", "phone_number", "profile_image"])
    new_id = get_next_id(df, "player_id")
    new_row = {"player_id": new_id, **data}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_csv(df, path)
    return new_row

def update_player(sport: str, player_id: int, data: dict):
    path = get_csv_path(sport, "players")
    df = load_csv(path, ["player_id", "player_name", "team_id", "phone_number", "profile_image"])
    df['player_id'] = pd.to_numeric(df['player_id'], errors='coerce')
    idx = df.index[df['player_id'] == player_id].tolist()
    if not idx: return None
    for k, v in data.items(): df.at[idx[0], k] = v
    save_csv(df, path)
    return df.iloc[idx[0]].where(pd.notnull(df.iloc[idx[0]]), None).to_dict()

def delete_player(sport: str, player_id: int):
    path = get_csv_path(sport, "players")
    df = load_csv(path)
    if "player_id" in df.columns:
        df['player_id'] = pd.to_numeric(df['player_id'], errors='coerce')
        df = df[df['player_id'] != player_id]
        save_csv(df, path)
    return {"status": "deleted"}

def get_matches(sport: str, tournament_id: int = None):
    path = get_csv_path(sport, "matches")
    cols = ["match_id", "tournament_id", "team1_id", "team2_id", "match_date", "venue"]
    if sport == "cricket": cols.append("overs_per_innings")
    df = load_csv(path, cols)
    if tournament_id is not None and not df.empty and "tournament_id" in df.columns:
        df['tournament_id'] = pd.to_numeric(df['tournament_id'], errors='coerce')
        df = df[df["tournament_id"] == tournament_id]
    return clean_records(df.to_dict(orient="records"))

def add_match(sport: str, data: dict):
    path = get_csv_path(sport, "matches")
    cols = ["match_id", "tournament_id", "team1_id", "team2_id", "match_date", "venue"]
    if sport == "cricket": cols.append("overs_per_innings")
    df = load_csv(path, cols)
    new_id = get_next_id(df, "match_id")
    new_row = {"match_id": new_id, **data}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_csv(df, path)
    return new_row

def delete_match(sport: str, match_id: int):
    path = get_csv_path(sport, "matches")
    df = load_csv(path)
    if "match_id" in df.columns:
        df['match_id'] = pd.to_numeric(df['match_id'], errors='coerce')
        df = df[df['match_id'] != match_id]
        save_csv(df, path)
    return {"status": "deleted"}

def get_scores(sport: str, match_id: int = None):
    path = get_csv_path(sport, "scores")
    df = load_csv(path)
    if match_id is not None and not df.empty and "match_id" in df.columns:
        df['match_id'] = pd.to_numeric(df['match_id'], errors='coerce')
        df = df[df["match_id"] == match_id]
    return clean_records(df.to_dict(orient="records"))

def add_score(sport: str, data: dict):
    path = get_csv_path(sport, "scores")
    df = load_csv(path)
    if df.empty:
        df = pd.DataFrame(columns=list(data.keys()))
    df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    save_csv(df, path)
    return data

def get_stats(sport: str, tournament_id: int = None):
    matches = get_matches(sport, tournament_id)
    match_ids = [m.get("match_id") for m in matches if m.get("match_id")]
    scores = []
    if match_ids:
        all_scores = get_scores(sport)
        scores = [s for s in all_scores if s.get("match_id") in match_ids]
    return {
        "matches": matches,
        "scores": scores,
        "players": get_players(sport),
        "teams": get_teams(sport),
        "tournaments": get_tournaments(sport)
    }
