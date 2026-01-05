import os
import joblib
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, accuracy_score
import numpy as np

DATA_PATH = "sports_dashboard/data"
TOURNAMENTS_CSV = os.path.join(DATA_PATH, "cricket_tournaments.csv")
TEAMS_CSV = os.path.join(DATA_PATH, "cricket_teams.csv")
PLAYERS_CSV = os.path.join(DATA_PATH, "cricket_players.csv")
MATCHES_CSV = os.path.join(DATA_PATH, "cricket_matches.csv")
SCORES_CSV = os.path.join(DATA_PATH, "cricket_scores.csv")


def ensure_data_path():
    os.makedirs(DATA_PATH, exist_ok=True)

def load_csv(path, columns=None):
    if os.path.exists(path):
        df = pd.read_csv(path)
        df.columns = df.columns.str.strip()
        return df
    else:
        return pd.DataFrame(columns=columns) if columns else pd.DataFrame()

def save_csv(df, path):
    ensure_data_path()
    df.to_csv(path, index=False)

def safe_rerun():
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            pass

def add_tournament():
    st.header("➕ Add Cricket Tournament")
    tournaments = load_csv(
        TOURNAMENTS_CSV,
        ["tournament_id", "tournament_name", "start_date", "end_date", "location"]
    )

    name = st.text_input("Tournament Name")
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")
    location = st.text_input("Location")

    if st.button("Add Tournament"):
        if not name:
            st.warning("Please enter a tournament name.")
            return

        new_id = tournaments["tournament_id"].max() + 1 if not tournaments.empty else 1
        new_row = pd.DataFrame(
            [[new_id, name, start_date, end_date, location]],
            columns=["tournament_id", "tournament_name", "start_date", "end_date", "location"]
        )
        tournaments = pd.concat([tournaments, new_row], ignore_index=True)
        save_csv(tournaments, TOURNAMENTS_CSV)
        st.success(f"Tournament '{name}' added successfully!")

def add_team():
    st.subheader("➕ Add Team")
    teams = load_csv(TEAMS_CSV, ["team_id", "team_name", "tournament_id"])
    tournaments = load_csv(
        TOURNAMENTS_CSV,
        ["tournament_id", "tournament_name", "start_date", "end_date", "location"]
    )

    if tournaments.empty:
        st.warning("No tournaments found. Please add a tournament first.")
        return
    team_name = st.text_input("Team Name")
    tournament_name = st.selectbox("Tournament", tournaments["tournament_name"].tolist())
    selected_tournament = tournaments[tournaments["tournament_name"] == tournament_name]

    if selected_tournament.empty:
        st.warning("Selected tournament not found. Please add a tournament first.")
        return

    tournament_id = selected_tournament["tournament_id"].values[0]

    if st.button("Add Team") and team_name:
        team_id = teams["team_id"].max() + 1 if not teams.empty else 1
        new_row = pd.DataFrame(
            [[team_id, team_name, tournament_id]],
            columns=["team_id", "team_name", "tournament_id"]
        )
        teams = pd.concat([teams, new_row], ignore_index=True)
        save_csv(teams, TEAMS_CSV)
        st.success(f"Team '{team_name}' added successfully!")

def add_players():
    st.subheader("➕ Add Player")
    players = load_csv(PLAYERS_CSV, ["player_id", "player_name", "team_id"])
    teams = load_csv(TEAMS_CSV, ["team_id", "team_name", "tournament_id"])

    if teams.empty:
        st.warning("No teams found. Please add a team first.")
        return

    player_name = st.text_input("Player Name")
    team_name = st.selectbox("Select Team", teams["team_name"].tolist())
    selected_team = teams[teams["team_name"] == team_name]

    if selected_team.empty:
        st.warning("Selected team not found. Please add a team first.")
        return

    team_id = int(selected_team["team_id"].values[0])

    if st.button("Add Player") and player_name:
        player_id = int(players["player_id"].max() + 1) if not players.empty else 1
        new_row = pd.DataFrame(
            [[player_id, player_name, team_id]],
            columns=["player_id", "player_name", "team_id"]
        )
        players = pd.concat([players, new_row], ignore_index=True)
        save_csv(players, PLAYERS_CSV)
        st.success(f"Player '{player_name}' added successfully!")
def schedule_match():
    st.subheader("📅 Schedule Match")

    tournaments = load_csv(TOURNAMENTS_CSV, ["tournament_id", "tournament_name"])
    teams = load_csv(TEAMS_CSV, ["team_id", "team_name", "tournament_id"])
    matches = load_csv(
        MATCHES_CSV,
        ["match_id", "tournament_id", "team1_id", "team2_id", "match_date", "venue", "overs_per_innings"]
    )

    if tournaments.empty:
        st.warning("No tournaments found. Add a tournament first.")
        return

    if teams.empty:
        st.warning("No teams found. Add teams first.")
        return

    tournament_name = st.selectbox("Tournament", tournaments["tournament_name"].tolist())
    selected_tournament = tournaments[tournaments["tournament_name"] == tournament_name]
    tournament_id = int(selected_tournament["tournament_id"].values[0])

    teams_in_t = teams[teams["tournament_id"] == tournament_id]
    if teams_in_t.shape[0] < 2:
        st.warning("At least two teams required in this tournament. Add teams first.")
        return

    team_choices = teams_in_t["team_name"].tolist()
    team1 = st.selectbox("Team 1", team_choices)
    team2 = st.selectbox("Team 2", [t for t in team_choices if t != team1])

    team1_id = int(teams[teams["team_name"] == team1]["team_id"].values[0])
    team2_id = int(teams[teams["team_name"] == team2]["team_id"].values[0])

    match_date = st.date_input("Match Date")
    venue = st.text_input("Venue")
    overs_per_innings = st.number_input("Overs per Innings", min_value=1, max_value=50, value=20)

    if st.button("Schedule Match"):
        match_id = int(matches["match_id"].max() + 1) if not matches.empty else 1
        new_row = pd.DataFrame(
            [[match_id, tournament_id, team1_id, team2_id, match_date, venue, overs_per_innings]],
            columns=[
                "match_id", "tournament_id", "team1_id", "team2_id",
                "match_date", "venue", "overs_per_innings"
            ]
        )
        matches = pd.concat([matches, new_row], ignore_index=True)
        save_csv(matches, MATCHES_CSV)
        st.success(f"Match scheduled successfully! Match ID: {match_id}")

def view_tournaments():
    st.subheader("📋 View Tournaments")
    tournaments = load_csv(TOURNAMENTS_CSV)
    matches = load_csv(MATCHES_CSV)
    teams = load_csv(TEAMS_CSV)

    if tournaments.empty:
        st.warning("No tournaments found.")
        return

    tournament_names = tournaments["tournament_name"].tolist()
    selected_tournament = st.selectbox("Select Tournament", tournament_names)

    if selected_tournament:
        st.markdown(f"### Matches in {selected_tournament}")
        tournament_id = int(
            tournaments.loc[tournaments["tournament_name"] == selected_tournament, "tournament_id"].values[0]
        )
        tournament_matches = matches[matches["tournament_id"] == tournament_id]

        if tournament_matches.empty:
            st.info("No matches scheduled for this tournament yet.")
        else:
            def get_team_name(team_id):
                name = teams.loc[teams["team_id"] == team_id, "team_name"]
                return name.values[0] if not name.empty else "Unknown"

            display_df = tournament_matches.copy()
            display_df["Team 1"] = display_df["team1_id"].apply(get_team_name)
            display_df["Team 2"] = display_df["team2_id"].apply(get_team_name)
            display_df["Match Date"] = display_df["match_date"]
            display_df["Venue"] = display_df["venue"]

            st.dataframe(
                display_df[["match_id", "Team 1", "Team 2", "Match Date", "Venue"]].reset_index(drop=True)
            )

def update_score():
    st.set_page_config(page_title="Live Cricket Scoring", layout="wide")
    st.title("🏏 Live Cricket Scoring")

    if not (os.path.exists(MATCHES_CSV) and os.path.exists(PLAYERS_CSV) and os.path.exists(TEAMS_CSV)):
        st.warning("Please add tournaments, teams, players and schedule matches first.")
        return

    matches = load_csv(MATCHES_CSV)
    players = load_csv(PLAYERS_CSV)
    teams = load_csv(TEAMS_CSV)
    tournaments = load_csv(TOURNAMENTS_CSV)
    scores = load_csv(
        SCORES_CSV,
        [
            "match_id", "innings", "over", "ball", "striker", "non_striker",
            "bowler", "runs", "extras", "wicket", "wicket_type",
            "fielder", "runout_by", "batting_team"
        ]
    )

    tournament_names = tournaments["tournament_name"].unique()
    tournament_name = st.selectbox("Select Tournament", tournament_names)
    tournament_row = tournaments[tournaments["tournament_name"] == tournament_name]
    tournament_id = int(tournament_row["tournament_id"].iloc[0])

    tournament_matches = matches[matches["tournament_id"] == tournament_id]
    match_id = st.selectbox("Select Match", tournament_matches["match_id"].tolist())
    match_info = tournament_matches[tournament_matches["match_id"] == match_id].iloc[0]

    total_balls = int(match_info.overs_per_innings) * 6

    team1_id = match_info.team1_id
    team2_id = match_info.team2_id
    team1_name = teams.loc[teams["team_id"] == team1_id, "team_name"].values[0]
    team2_name = teams.loc[teams["team_id"] == team2_id, "team_name"].values[0]
    team1_players = players[players["team_id"] == team1_id]["player_name"].tolist()
    team2_players = players[players["team_id"] == team2_id]["player_name"].tolist()

    # Batting Team Selection Persisted in Session State
    if f"bat_first_{match_id}" not in st.session_state:
        st.subheader("🏏 Select Batting Team")
        bat_first = st.radio(
            "Which team will bat first?",
            [team1_name, team2_name],
            key=f"batfirst_{match_id}"
        )
        st.session_state[f"bat_first_{match_id}"] = bat_first
        st.session_state[f"bowl_first_{match_id}"] = (
            team2_name if bat_first == team1_name else team1_name
        )
    elif f"bat_first_{match_id}" in st.session_state:
        # If different match or changed context, re-ask
        if st.session_state[f"bat_first_{match_id}"] not in [team1_name, team2_name]:
            st.subheader("🏏 Select Batting Team")
            bat_first = st.radio(
                "Which team will bat first?",
                [team1_name, team2_name],
                key=f"batfirst_{match_id}"
            )
            st.session_state[f"bat_first_{match_id}"] = bat_first
            st.session_state[f"bowl_first_{match_id}"] = (
                team2_name if bat_first == team1_name else team1_name
            )

    bat_first = st.session_state[f"bat_first_{match_id}"]
    bowl_first = st.session_state[f"bowl_first_{match_id}"]

    # Filter all balls for selected match only
    scores_for_match = scores[scores["match_id"] == match_id]

    # Separate innings data for that match
    innings_1 = scores_for_match[scores_for_match["innings"] == 1]
    innings_2 = scores_for_match[scores_for_match["innings"] == 2]

    runs_1, wickets_1 = innings_1["runs"].sum(), (innings_1["wicket"] == "Yes").sum()
    balls_1 = legal_balls(innings_1).shape[0]

    runs_2, wickets_2 = innings_2["runs"].sum(), (innings_2["wicket"] == "Yes").sum()
    balls_2 = legal_balls(innings_2).shape[0]

    innings_1_complete = wickets_1 >= 10 or balls_1 >= total_balls
    innings_2_complete = wickets_2 >= 10 or balls_2 >= total_balls or runs_2 > runs_1

    # Determine current innings
    batting_team, bowling_team = None, None

    if not innings_1_complete:
        current_innings = 1
        batting_team = bat_first
        bowling_team = bowl_first
        batting_team_players = team1_players if bat_first == team1_name else team2_players
        bowling_team_players = team2_players if bat_first == team1_name else team1_players
        current_runs, current_wickets, current_balls = runs_1, wickets_1, balls_1

    elif not innings_2_complete:
        current_innings = 2
        batting_team = bowl_first
        bowling_team = bat_first
        batting_team_players = team2_players if bowl_first == team2_name else team1_players
        bowling_team_players = team1_players if bowl_first == team2_name else team2_players
        current_runs, current_wickets, current_balls = runs_2, wickets_2, balls_2

    else:
        current_innings = None
        # Match finished and display winner
        if innings_1_complete and innings_2_complete:
            st.markdown("### Match Completed")
            if runs_2 > runs_1:
                st.success(f"🏆 {bowl_first} won the match by {10 - wickets_2} wickets!")
            elif runs_1 > runs_2:
                st.success(f"🏆 {bat_first} won the match by {runs_1 - runs_2} runs!")
            else:
                st.info("🤝 The match is a tie!")
            return

    # Display current score
    if current_innings == 1:
        st.markdown(
            f"### {batting_team}: {runs_1}/{wickets_1} in {balls_1//6}.{balls_1%6} overs"
        )
    elif current_innings == 2:
        st.markdown(
            f"### {batting_team}: {runs_2}/{wickets_2} in {balls_2//6}.{balls_2%6} overs "
            f"(Target {runs_1 + 1})"
        )

    # ML Prediction Integration
    if current_innings is not None:
        fun()
        balls_left = total_balls - current_balls
        wickets_left = 10 - current_wickets
        run_rate = current_runs / (current_balls / 6) if current_balls > 0 else 0

        features = [current_runs, current_wickets, balls_left, wickets_left, run_rate]
        regressor = joblib.load("score_predictor.pkl")
        classifier = joblib.load("win_predictor.pkl")

        try:
            st.info(
                f"🤖 current run rate: "
                f"{((current_runs / (total_balls - balls_left)) * 6):.2f}"
            )
            if current_innings == 1:
                st.info(
                    f"🤖 Predicted Final Score: "
                    f"{((current_runs / current_balls) * balls_left):.2f}"
                )
            else:
                st.info(
                    f"🤖 required run rate: "
                    f"{((((runs_1 + 1) - current_runs) / balls_left) * 6):.2f}"
                )
        except Exception as e:
            st.error(f"Prediction error: {e}")

        try:
            _ = classifier.predict_proba([features])[0]
            crr = ((current_runs / (total_balls - balls_left)) * 6)
            rrr = ((((runs_1 + 1) - current_runs) / balls_left) * 6)

            win_prob = 50 + (crr - rrr) * 10 - (wickets_2 * 2)
            win_prob = max(0, min(100, win_prob))

            col1, col2 = st.columns(2)
            col1.success(f"{batting_team}: {win_prob:.2f}%")
            col2.error(f"{bowling_team}: {100 - win_prob:.2f}%")
        except Exception as e:
            st.error(f"Win probability error: {e}")

    if current_innings is None:
        return

    # Player selections for current innings
    striker_key = f"striker_{match_id}_{current_innings}"
    nonstriker_key = f"non_striker_{match_id}_{current_innings}"
    bowler_key = f"bowler_{match_id}_{current_innings}"

    if striker_key not in st.session_state or st.session_state[striker_key] not in batting_team_players:
        st.session_state[striker_key] = batting_team_players[0] if batting_team_players else None

    if nonstriker_key not in st.session_state or st.session_state[nonstriker_key] not in batting_team_players:
        non_strikers = [p for p in batting_team_players if p != st.session_state[striker_key]]
        st.session_state[nonstriker_key] = non_strikers[0] if non_strikers else None

    if bowler_key not in st.session_state or st.session_state[bowler_key] not in bowling_team_players:
        st.session_state[bowler_key] = bowling_team_players[0] if bowling_team_players else None

    st.session_state[striker_key] = st.selectbox(
        "Striker",
        batting_team_players,
        index=batting_team_players.index(st.session_state[striker_key]),
        key=f"striker_sel_{match_id}_{current_innings}"
    )

    nonstriker_options = [p for p in batting_team_players if p != st.session_state[striker_key]]
    if nonstriker_options:
        st.session_state[nonstriker_key] = st.selectbox(
            "Non-Striker",
            nonstriker_options,
            index=0,
            key=f"nonstriker_sel_{match_id}_{current_innings}"
        )
    else:
        st.session_state[nonstriker_key] = None

    st.session_state[bowler_key] = st.selectbox(
        "Bowler",
        bowling_team_players,
        index=bowling_team_players.index(st.session_state[bowler_key]),
        key=f"bowler_sel_{match_id}_{current_innings}"
    )

    st.markdown(
        f"**Striker:** {st.session_state[striker_key]} | "
        f"**Non-Striker:** {st.session_state[nonstriker_key]} | "
        f"**Bowler:** {st.session_state[bowler_key]}"
    )

    runs = st.number_input(
        "Runs", 0, 6, 0,
        key=f"runs_{match_id}_{current_innings}"
    )
    extras = st.selectbox(
        "Extras",
        ["None", "Wide", "No Ball", "Bye", "Leg Bye"],
        key=f"extras_{match_id}_{current_innings}"
    )
    wicket = st.radio(
        "Wicket?",
        ["No", "Yes"],
        key=f"wicket_{match_id}_{current_innings}"
    )

    wicket_type = None
    out_batsman = None

    if wicket == "Yes":
        wicket_type = st.selectbox(
            "Type",
            ["Bowled", "Caught", "Stumped", "Run Out", "LBW", "Other"],
            key=f"wt_{match_id}_{current_innings}"
        )
        out_batsman = st.selectbox(
            "Who is out?",
            [st.session_state[striker_key], st.session_state[nonstriker_key]],
            key=f"out_{match_id}_{current_innings}"
        )

    if st.button("Submit Ball"):
        new_ball = {
            "match_id": match_id,
            "innings": current_innings,
            "over": current_balls // 6,
            "ball": current_balls % 6 + 1,
            "striker": st.session_state[striker_key],
            "non_striker": st.session_state[nonstriker_key],
            "bowler": st.session_state[bowler_key],
            "runs": runs,
            "extras": extras if extras != "None" else "",
            "wicket": wicket,
            "wicket_type": wicket_type or "",
            "fielder": "",
            "runout_by": "",
            "batting_team": batting_team
        }

        scores = pd.concat([scores, pd.DataFrame([new_ball])], ignore_index=True)

        if wicket == "Yes":
            available = [
                p for p in batting_team_players
                if p not in [st.session_state[striker_key], st.session_state[nonstriker_key]]
            ]
            if available:
                st.session_state[striker_key] = st.selectbox(
                    "New Striker",
                    available,
                    key=f"newstriker_{match_id}_{current_innings}"
                )
        else:
            if extras not in ["Wide", "No Ball"] and runs % 2 == 1:
                (
                    st.session_state[striker_key],
                    st.session_state[nonstriker_key]
                ) = (
                    st.session_state[nonstriker_key],
                    st.session_state[striker_key]
                )

        balls_faced = legal_balls(
            scores[(scores["match_id"] == match_id) & (scores["innings"] == current_innings)]
        ).shape[0]

        if balls_faced % 6 == 0 and balls_faced != 0:
            (
                st.session_state[striker_key],
                st.session_state[nonstriker_key]
            ) = (
                st.session_state[nonstriker_key],
                st.session_state[striker_key]
            )
            st.info("🔄 End of Over – Striker and Non-Striker swapped automatically.")
            st.session_state[bowler_key] = st.selectbox(
                "Select Next Over Bowler",
                [p for p in bowling_team_players if p != st.session_state[bowler_key]],
                key=f"newbowler_{match_id}_{current_innings}_{current_balls}"
            )

        scores.to_csv(SCORES_CSV, index=False)
        st.success("Ball recorded ✅")

def fun():
    # uses your absolute path – keep as is if your data is here
    df = pd.read_csv("/home/apiiit123/projects/major_project_2/sports_dashboard/data/cricket_scores.csv")
    OVERS = 20
    TOTAL_BALLS = OVERS * 6

    df['balls_bowled'] = df['over'] * 6 + df['ball']
    df['runs'] = pd.to_numeric(df['runs'], errors='coerce')
    df['current_runs'] = df.groupby(['match_id', 'innings'])['runs'].cumsum()
    df['current_wickets'] = df.groupby(['match_id', 'innings'])['wicket'].transform(
        lambda x: x.eq('Yes').cumsum()
    )
    df['balls_left'] = TOTAL_BALLS - df['balls_bowled']
    df['wickets_left'] = 10 - df['current_wickets']
    df['run_rate'] = df['current_runs'] / (df['balls_bowled'] / 6)
    df.loc[df['balls_bowled'] == 0, 'run_rate'] = 0
    df['final_score'] = df.groupby(['match_id', 'innings'])['current_runs'].transform('max')
    df['target'] = df.apply(
        lambda row: 0 if row['innings'] == 1 else
        df[(df['match_id'] == row['match_id']) & (df['innings'] == 1)]['final_score'].max() + 1,
        axis=1
    )
    df['win'] = 0
    for match in df['match_id'].unique():
        final_score_1 = df[(df['match_id'] == match) & (df['innings'] == 1)]['final_score'].max()
        final_score_2 = df[(df['match_id'] == match) & (df['innings'] == 2)]['final_score'].max()
        if final_score_2 > final_score_1:
            df.loc[(df['match_id'] == match) & (df['innings'] == 2), 'win'] = 1

    features = ['current_runs', 'current_wickets', 'balls_left', 'wickets_left', 'run_rate']
    X_score = df[features]
    y_score = df['final_score']

    X_train_score, X_test_score, y_train_score, y_test_score = train_test_split(
        X_score, y_score, test_size=0.2, random_state=42
    )
    regressor = RandomForestRegressor(n_estimators=100, random_state=42)
    regressor.fit(X_train_score, y_train_score)
    _ = regressor.predict(X_test_score)

    df_inn2 = df[df['innings'] == 2].copy()
    X_win = df_inn2[features]
    y_win = df_inn2['win']
    X_train_win, X_test_win, y_train_win, y_test_win = train_test_split(
        X_win, y_win, test_size=0.2, random_state=42
    )
    classifier = RandomForestClassifier(n_estimators=100, random_state=42)
    classifier.fit(X_train_win, y_train_win)
    _ = classifier.predict(X_test_win)

    joblib.dump(regressor, "/home/apiiit123/projects/major_project_2/score_predictor.pkl")
    joblib.dump(classifier, "/home/apiiit123/projects/major_project_2/win_predictor.pkl")

def match_summary():
    st.header("📊 Match Summary")

    tournaments = load_csv(TOURNAMENTS_CSV)
    matches = load_csv(MATCHES_CSV)
    scores = load_csv(SCORES_CSV)
    teams = load_csv(TEAMS_CSV)

    if tournaments.empty:
        st.warning("No tournaments file found.")
        return

    tournament_names = tournaments["tournament_name"].unique()
    tournament_name = st.selectbox("Select Tournament", tournament_names)
    tournament_row = tournaments[tournaments["tournament_name"] == tournament_name]
    tournament_id = int(tournament_row["tournament_id"].iloc[0])

    tournament_matches = matches[matches["tournament_id"] == tournament_id]
    if tournament_matches.empty:
        st.info("No scheduled matches for selected tournament.")
        return

    match_id = st.selectbox("Select Match", tournament_matches["match_id"].tolist())
    match_row = tournament_matches[tournament_matches["match_id"] == match_id].iloc[0]

    team1_id = int(match_row["team1_id"])
    team2_id = int(match_row["team2_id"])

    team1_name = teams.loc[teams["team_id"] == team1_id, "team_name"].values[0]
    team2_name = teams.loc[teams["team_id"] == team2_id, "team_name"].values[0]

    if "match_id" not in scores.columns:
        st.error("Scores file must contain 'match_id' column.")
        return

    df = scores[scores["match_id"] == match_id].copy()
    if df.empty:
        st.info("No ball-by-ball data for this match yet.")
        return

    # casting
    df["over"] = df["over"].astype(int)
    df["ball"] = df["ball"].astype(int)
    df["runs"] = pd.to_numeric(df["runs"], errors="coerce").fillna(0).astype(int)

    # --- Batting summary ---
    def batting_summary_table(df_team, team_name):
        st.subheader(f"🏏 Batting Summary - {team_name}")
        df_team["Ball_no"] = (df_team["over"] * 6 + df_team["ball"]).astype(int)
        df_team["Dismissal"] = df_team["wicket"].apply(lambda x: 1 if x == "Yes" else 0)
        summary = df_team.groupby("striker").agg(
            {"runs": "sum", "Ball_no": "count", "Dismissal": "sum"}
        ).rename_axis(None).reset_index()
        summary["Strike Rate"] = round(summary["runs"] / summary["Ball_no"] * 100, 2)
        summary["Average"] = round(summary["runs"] / summary["Dismissal"].replace(0, 1), 2)
        st.dataframe(summary)

    team1_df = df[df["batting_team"] == team1_name].copy()
    team2_df = df[df["batting_team"] == team2_name].copy()

    batting_summary_table(team1_df, team1_name)
    batting_summary_table(team2_df, team2_name)

    # --- Runs per over comparison ---
    st.subheader("📊 Runs per Over Comparison (both teams)")
    runs_over = df.groupby(["batting_team", "over"])["runs"].sum().reset_index()
    wickets_over = df[df["wicket"] == "Yes"].groupby(
        ["batting_team", "over"]
    )["wicket"].count().reset_index().rename(columns={"wicket": "wickets"})

    teams_order = [team1_name, team2_name]
    max_over = int(df["over"].max())

    fig, ax = plt.subplots(figsize=(10, 5))
    width = 0.35
    x = range(0, max_over + 1)

    for i, t in enumerate(teams_order):
        arr = []
        wk = []
        for over in x:
            val = runs_over[(runs_over["batting_team"] == t) & (runs_over["over"] == over)]["runs"]
            arr.append(int(val.iloc[0]) if not val.empty else 0)
            wval = wickets_over[
                (wickets_over["batting_team"] == t) & (wickets_over["over"] == over)
            ]["wickets"]
            wk.append(int(wval.iloc[0]) if not wval.empty else 0)
        positions = [ov + (i - 0.5) * width for ov in x]
        ax.bar(positions, arr, width=width, label=t)
        for ov_idx, wcount in enumerate(wk):
            if wcount > 0:
                ax.scatter(
                    positions[ov_idx],
                    arr[ov_idx] + 0.3,
                    s=50 + 50 * wcount,
                    c='red',
                    zorder=5
                )

    ax.set_xlabel("Over")
    ax.set_ylabel("Runs")
    ax.set_title("Runs per Over (comparison)")
    ax.legend()
    ax.set_xticks(range(0, max_over + 1))
    st.pyplot(fig)

    # --- Cumulative score progression ---
    st.subheader("📈 Cumulative Score Progression")
    fig2, ax2 = plt.subplots(figsize=(10, 5))

    for t in teams_order:
        t_df = runs_over[runs_over["batting_team"] == t].set_index("over").reindex(
            range(0, max_over + 1), fill_value=0
        )["runs"].cumsum()
        ax2.plot(range(0, max_over + 1), t_df, marker='o', label=t)

    ax2.set_xlabel("Over")
    ax2.set_ylabel("Cumulative Runs")
    ax2.legend()
    ax2.set_xticks(range(0, max_over + 1))
    st.pyplot(fig2)

    st.subheader("🏆 Match Awards")

    total_balls = int(match_row["overs_per_innings"]) * 6

    innings_1 = df[df["innings"] == 1]
    innings_2 = df[df["innings"] == 2]

    runs_1 = innings_1["runs"].sum()
    runs_2 = innings_2["runs"].sum()
    wickets_1 = (innings_1["wicket"] == "Yes").sum()
    wickets_2 = (innings_2["wicket"] == "Yes").sum()
    balls_1 = legal_balls(innings_1).shape[0]
    balls_2 = legal_balls(innings_2).shape[0]

    innings_1_done = wickets_1 >= 10 or balls_1 >= total_balls
    innings_2_done = wickets_2 >= 10 or balls_2 >= total_balls or runs_2 > runs_1

    if not (innings_1_done and innings_2_done):
        st.warning("🏏 Match is still LIVE – Awards will be shown once both innings are completed.")
        return

    awards = compute_cricket_awards(match_id)
    if awards:
        stats, best_bowl = awards

        # Best Player (MVP)
        best_player = stats.iloc[0]
        st.success(
            f"🥇 Best Player: **{best_player['player_name']}** — "
            f"MVP Score: {best_player['mvp_score']:.1f}, "
            f"Runs: {best_player['runs']}, "
            f"Wickets: {best_player['wickets']}"
        )

        # Best Bowler
        best_bowler = best_bowl.iloc[0]
        st.info(
            f"🎯 Best Bowler: **{best_bowler['player_name']}** — "
            f"{best_bowler['wickets']} wickets, Econ {best_bowler['economy']:.2f}"
        )

        # Star Performers (Top 3)
        st.markdown("🌟 **Star Performers – Top 3**")
        st.dataframe(
            stats[[
                "player_name", "runs", "wickets", "catches",
                "strike_rate", "economy", "mvp_score"
            ]].head(3).reset_index(drop=True)
        )

def legal_balls(innings_df):
    if 'extras_type' in innings_df.columns:
        legal = innings_df[~innings_df['extras_type'].isin(['wide', 'no-ball'])]
    elif 'extras' in innings_df.columns:
        # NOTE: Extras are stored capitalized (Wide/No Ball), adjust if needed
        legal = innings_df[~innings_df['extras'].isin(['wide', 'no-ball'])]
    else:
        legal = innings_df
    return legal

def compute_cricket_awards(match_id):
    scores = load_csv(SCORES_CSV)
    if scores.empty:
        return None

    df = scores[scores["match_id"] == match_id].copy()
    if df.empty:
        return None
    # Normalise runs
    df["runs"] = pd.to_numeric(df["runs"], errors="coerce").fillna(0).astype(int)
    # Batting stats
    bat = df.groupby("striker").agg(
        runs=("runs", "sum"),
        balls=("ball", "count")
    ).reset_index().rename(columns={"striker": "player_name"})
    bat["balls"] = bat["balls"].replace(0, 1)
    bat["strike_rate"] = (bat["runs"] / bat["balls"]) * 100
    # Bowling stats
    legal = legal_balls(df)
    bowl_balls = legal.groupby("bowler")["ball"].count().reset_index().rename(
        columns={"bowler": "player_name", "ball": "balls_bowled"}
    )
    bowl_runs = df.groupby("bowler")["runs"].sum().reset_index().rename(
        columns={"bowler": "player_name", "runs": "runs_conceded"}
    )
    bowl_wkts = df[df["wicket"] == "Yes"].groupby("bowler")["wicket"].count().reset_index().rename(
        columns={"bowler": "player_name", "wicket": "wickets"}
    )

    bowl = pd.merge(bowl_balls, bowl_runs, how="outer", on="player_name")
    bowl = pd.merge(bowl, bowl_wkts, how="outer", on="player_name").fillna(0)
    bowl["overs"] = bowl["balls_bowled"] / 6.0
    bowl["overs"] = bowl["overs"].replace(0, 1e-9)
    bowl["economy"] = bowl["runs_conceded"] / bowl["overs"]

    # Catches (fielder)
    if "fielder" in df.columns:
        catches = df[df["fielder"] != ""]
        # Count best fielder by number of catches
        catches = catches.groupby("fielder")["fielder"].count().reset_index(name="catches")
        # Rename fielder → player_id for consistency
        catches = catches.rename(columns={"fielder": "player_id"})
        catches.columns = ["player_name", "catches"]
    else:
        catches = pd.DataFrame(columns=["player_name", "catches"])

    # Merge all
    stats = pd.merge(bat, bowl, how="outer", on="player_name")
    stats = pd.merge(stats, catches, how="outer", on="player_name").fillna(0)

    # types
    for col in ["runs", "balls", "balls_bowled", "runs_conceded", "wickets", "catches"]:
        stats[col] = stats[col].astype(int)

    for col in ["strike_rate", "economy"]:
        stats[col] = pd.to_numeric(stats[col], errors="coerce").fillna(0.0)

    # Advanced MVP formula
    stats["strike_rate_factor"] = (stats["strike_rate"] - 100.0) / 5.0
    stats["economy_factor"] = (stats["economy"] - 6.0) * 2.0
    stats["mvp_score"] = (
        stats["runs"] * 1.2 +
        stats["wickets"] * 15 +
        stats["catches"] * 8 +
        stats["strike_rate_factor"] -
        stats["economy_factor"]
    )

    stats = stats.sort_values("mvp_score", ascending=False).reset_index(drop=True)

    best_bowl = stats.sort_values(["wickets", "economy"], ascending=[False, True]).reset_index(drop=True)

    return stats, best_bowl

def c_run():
    st.title(" 🏏 Cricket Dashboard")
    st.write("Live cricket stats go here...")
def run_cricket():
    st.sidebar.title("🏏 Cricket Module")
    options = [
        "Add Tournament", "Add Team", "Add Player to Team",
        "View Tournaments", "Schedule Match",
        "Update Live Score", "View Match Summary"
    ]
    choice = st.sidebar.radio("Choose Option", options)

    if choice == "Add Tournament":
        add_tournament()
    elif choice == "Add Team":
        add_team()
    elif choice == "Add Player to Team":
        add_players()
    elif choice == "View Tournaments":
        view_tournaments()
    elif choice == "Schedule Match":
        schedule_match()
    elif choice == "Update Live Score":
        update_score()
    elif choice == "View Match Summary":
        match_summary()

