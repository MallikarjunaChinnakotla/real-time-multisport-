import os
import pandas as pd

# Base directory for all sports data
BASE_DIR = "sports_data/data"

# Structure: sport → csv filename → csv headers
SPORTS_STRUCTURE = {
    "handball": {
        "handball_teams.csv": ["team_name", "players"],
        "handball_tournaments.csv": ["name", "location", "date"],
        "handball_matches.csv": ["tournament", "team1", "team2", "date"],
        "handball_scores.csv": ["match", "team1", "team2", "score1", "score2",
                                "serve_team", "timeout_team", "timestamp"],
    },
    "table_tennis": {
        "tt_teams.csv": ["team_name", "players"],
        "tt_tournaments.csv": ["name", "location", "date"],
        "tt_matches.csv": ["tournament", "team1", "team2", "date"],
        "tt_scores.csv": ["match", "team1", "team2", "score1", "score2",
                          "serve_team", "timeout_team", "timestamp"],
    },
    "hockey": {
        "hockey_teams.csv": ["team_name", "players"],
        "hockey_tournaments.csv": ["name", "location", "date"],
        "hockey_matches.csv": ["tournament", "team1", "team2", "date"],
        "hockey_scores.csv": ["match", "team1", "team2", "score1", "score2",
                              "serve_team", "timeout_team", "timestamp"],
    },
    "softball": {
        "softball_teams.csv": ["team_name", "players"],
        "softball_tournaments.csv": ["name", "location", "date"],
        "softball_matches.csv": ["tournament", "team1", "team2", "date"],
        "softball_scores.csv": ["match", "team1", "team2", "score1", "score2",
                                "serve_team", "timeout_team", "timestamp"],
    }
}


def init_csv_files():
    """Create all CSV folders/files with headers if missing"""
    for sport, files in SPORTS_STRUCTURE.items():
        sport_folder = os.path.join(BASE_DIR, sport)
        os.makedirs(sport_folder, exist_ok=True)

        print(f"📂 Checking: {sport_folder}")

        for filename, headers in files.items():
            path = os.path.join(sport_folder, filename)

            if not os.path.exists(path) or os.path.getsize(path) == 0:
                print(f"  ➤ Creating {filename} with headers")
                pd.DataFrame(columns=headers).to_csv(path, index=False)
            else:
                print(f"  ✔ Exists: {filename}")

    print("\nAll files initialized successfully! ✅")


if __name__ == "__main__":
    init_csv_files()

