import os
import joblib
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, accuracy_score
import numpy as np
import datetime

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

    tournaments = load_csv(
        TOURNAMENTS_CSV,
        ["tournament_id", "tournament_name", "start_date", "end_date", "location"]
    )

    if teams.empty:
        st.warning("No teams found. Please add a team first.")
        return
    
    if tournaments.empty:
        st.warning("No tournaments found. Please add a tournament first.")
        return

    player_name = st.text_input("Player Name")
    
    # Filter teams by tournament
    tournament_name = st.selectbox("Select Tournament", tournaments["tournament_name"].tolist())
    selected_tournament = tournaments[tournaments["tournament_name"] == tournament_name]
    
    if not selected_tournament.empty:
        tournament_id = selected_tournament["tournament_id"].values[0]
        filtered_teams = teams[teams["tournament_id"] == tournament_id]
        
        if filtered_teams.empty:
            st.info(f"No teams found in {tournament_name}.")
            return
            
        team_name = st.selectbox("Select Team", filtered_teams["team_name"].tolist())
        selected_team = filtered_teams[filtered_teams["team_name"] == team_name]

        if selected_team.empty:
            st.warning("Selected team not found.")
            return

        team_id = int(selected_team["team_id"].values[0])
        
        phone_number = st.text_input("Player Phone Number")
        uploaded_file = st.file_uploader("Upload Player Photo", type=['jpg', 'jpeg', 'png'])

        if st.button("Add Player") and player_name:
            player_id = int(players["player_id"].max() + 1) if not players.empty else 1
            
            # Check if columns exist, if not create them
            if "phone_number" not in players.columns:
                players["phone_number"] = ""
            if "profile_image" not in players.columns:
                players["profile_image"] = ""
                
            image_path = ""
            if uploaded_file is not None:
                img_dir = os.path.join(DATA_PATH, "cricket_player_images")
                os.makedirs(img_dir, exist_ok=True)
                
                timestamp = int(datetime.datetime.now().timestamp())
                # Sanitize filename
                safe_name = "".join(x for x in player_name if x.isalnum())
                ext = uploaded_file.name.split('.')[-1]
                filename = f"{player_id}_{safe_name}_{timestamp}.{ext}"
                save_path = os.path.join(img_dir, filename)
                
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                image_path = save_path
                
            new_row = pd.DataFrame(
                [[player_id, player_name, team_id, str(phone_number), image_path]],
                columns=["player_id", "player_name", "team_id", "phone_number", "profile_image"]
            )
            players = pd.concat([players, new_row], ignore_index=True)
            save_csv(players, PLAYERS_CSV)
            st.success(f"Player '{player_name}' added successfully to {team_name}!")
            if image_path:
                st.image(image_path, caption="Uploaded Photo", width=150)
    else:
        st.warning("Tournament not found")
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
        
        # Calculate Tournament Match Index
        count_in_tourney = matches[matches["tournament_id"] == tournament_id].shape[0]
        st.success(f"Match scheduled successfully! {tournament_name} Match #{count_in_tourney}")

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

            display_df = tournament_matches.copy().reset_index(drop=True)
            display_df.index += 1
            display_df["Match #"] = display_df.index
            
            display_df["Team 1"] = display_df["team1_id"].apply(get_team_name)
            display_df["Team 2"] = display_df["team2_id"].apply(get_team_name)
            display_df["Match Date"] = display_df["match_date"]
            display_df["Venue"] = display_df["venue"]

            st.dataframe(
                display_df[["Match #", "Team 1", "Team 2", "Match Date", "Venue"]]
            )
            
            # --- Tournament Statistics / Awards ---
            st.divider()
            st.subheader("🏆 Tournament Hub & Statistics")
            
            if st.button("📊 Generate Player of the Series & Stats"):
                leaderboard = compute_tournament_awards(tournament_id)
                
                if leaderboard is not None and not leaderboard.empty:
                    # Merge Player Images
                    players_df = load_csv(PLAYERS_CSV)
                    if not players_df.empty and "profile_image" in players_df.columns:
                        # Deduplicate by name to prevent merge issues (taking first found)
                        p_imgs = players_df[["player_name", "profile_image"]].drop_duplicates("player_name")
                        leaderboard = pd.merge(leaderboard, p_imgs, on="player_name", how="left")
                    
                    # Helper to get image
                    def get_img(row):
                        default_img = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
                        if "profile_image" in row and pd.notna(row["profile_image"]) and row["profile_image"]:
                            if os.path.exists(row["profile_image"]):
                                return row["profile_image"]
                        return default_img

                    # Best Player (Series MVP)
                    top_player = leaderboard.iloc[0]
                    mvp_img = get_img(top_player)
                    
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.markdown("### 🏅 Player of the Series")
                        st.image(mvp_img, width=150, caption=top_player['player_name'])
                    with c2:
                        st.markdown(f"## **{top_player['player_name']}**")
                        st.markdown(f"**MVP Score: {top_player['mvp_score']:.1f}**")
                        st.caption(f"Runs: {top_player['runs']} | Wickets: {top_player['wickets']} | Catches: {top_player['catches']}")
                        
                    st.divider()
                    
                    # Top Batsman & Bowler Layout
                    col_bat, col_bowl = st.columns(2)
                    
                    # Top Batsman (Most Runs)
                    best_bat = leaderboard.sort_values("runs", ascending=False).iloc[0]
                    bat_img = get_img(best_bat)
                    with col_bat:
                        st.markdown(f"#### 🏏 Best Batsman")
                        st.image(bat_img, width=100)
                        st.markdown(f"**{best_bat['player_name']}**") 
                        st.markdown(f"**{best_bat['runs']} Runs**")

                    # Top Bowler (Most Wickets)
                    best_bowl = leaderboard.sort_values(["wickets", "economy"], ascending=[False, True]).iloc[0]
                    bowl_img = get_img(best_bowl)
                    with col_bowl:
                        st.markdown(f"#### 🎯 Best Bowler")
                        st.image(bowl_img, width=100)
                        st.markdown(f"**{best_bowl['player_name']}**")
                        st.markdown(f"**{best_bowl['wickets']} Wickets**")
                    
                    st.subheader("📋 Series Leaderboard")
                    st.dataframe(leaderboard[["player_name", "runs", "wickets", "catches", "strike_rate", "economy", "mvp_score"]].head(10))
                else:
                    st.warning("Not enough data to calculate series awards yet.")

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
    
    # Ensure ID columns are integers
    if not players.empty:
        players["team_id"] = pd.to_numeric(players["team_id"], errors="coerce").fillna(-1).astype(int)
    if not matches.empty:
        matches["team1_id"] = pd.to_numeric(matches["team1_id"], errors="coerce").fillna(-1).astype(int)
        matches["team2_id"] = pd.to_numeric(matches["team2_id"], errors="coerce").fillna(-1).astype(int)
        
    # Ensure runs are numeric to prevent calculation errors
    if not scores.empty:
        scores["runs"] = pd.to_numeric(scores["runs"], errors="coerce").fillna(0).astype(int)
        scores["over"] = pd.to_numeric(scores["over"], errors="coerce").fillna(0).astype(int)
        scores["ball"] = pd.to_numeric(scores["ball"], errors="coerce").fillna(0).astype(int)
        scores["innings"] = pd.to_numeric(scores["innings"], errors="coerce").fillna(1).astype(int)

    tournament_names = tournaments["tournament_name"].unique()
    tournament_name = st.selectbox("Select Tournament", tournament_names)
    tournament_row = tournaments[tournaments["tournament_name"] == tournament_name]
    tournament_id = int(tournament_row["tournament_id"].iloc[0])

    tournament_matches = matches[matches["tournament_id"] == tournament_id].reset_index(drop=True)
    
    if tournament_matches.empty:
        st.warning(f"No matches scheduled for {tournament_name}.")
        return

    # Create proper options mapping Display Name -> Match ID
    match_options = {}
    for idx, row in tournament_matches.iterrows():
        t1 = teams.loc[teams["team_id"] == row["team1_id"], "team_name"].values[0] if not teams[teams["team_id"] == row["team1_id"]].empty else "Unknown"
        t2 = teams.loc[teams["team_id"] == row["team2_id"], "team_name"].values[0] if not teams[teams["team_id"] == row["team2_id"]].empty else "Unknown"
        label = f"Match {idx + 1}: {t1} vs {t2}"
        match_options[label] = row["match_id"]
        
    selected_label = st.selectbox("Select Match", list(match_options.keys()))
    match_id = match_options[selected_label]
    match_info = tournament_matches[tournament_matches["match_id"] == match_id].iloc[0]

    total_balls = int(match_info.overs_per_innings) * 6

    team1_id = int(match_info.team1_id)
    team2_id = int(match_info.team2_id)
    team1_name = teams.loc[teams["team_id"] == team1_id, "team_name"].values[0]
    team2_name = teams.loc[teams["team_id"] == team2_id, "team_name"].values[0]
    
    # Strict filtering
    team1_players = list(set(players[players["team_id"] == team1_id]["player_name"].tolist()))
    team2_players = list(set(players[players["team_id"] == team2_id]["player_name"].tolist()))


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

    # --- FIX: Deferred State Reset ---
    if st.session_state.get(f"reset_{striker_key}"):
        if striker_key in st.session_state:
            del st.session_state[striker_key]
        del st.session_state[f"reset_{striker_key}"]

    if st.session_state.get(f"reset_{nonstriker_key}"):
        if nonstriker_key in st.session_state:
            del st.session_state[nonstriker_key]
        del st.session_state[f"reset_{nonstriker_key}"]
    # ---------------------------------

    if striker_key not in st.session_state or st.session_state[striker_key] not in batting_team_players:
        st.session_state[striker_key] = batting_team_players[0] if batting_team_players else None

    if nonstriker_key not in st.session_state or st.session_state[nonstriker_key] not in batting_team_players:
        non_strikers = [p for p in batting_team_players if p != st.session_state[striker_key]]
        st.session_state[nonstriker_key] = non_strikers[0] if non_strikers else None

    if bowler_key not in st.session_state or st.session_state[bowler_key] not in bowling_team_players:
        st.session_state[bowler_key] = bowling_team_players[0] if bowling_team_players else None

    # Calculate Live Stats
    # 1. Batter Stats (Runs/Balls)
    # Filter for current match only
    match_scores_df = matches_data_df = scores[scores["match_id"] == match_id]
    
    def get_batter_stats(player_name):
        if not player_name: return 0, 0
        # Runs: All runs scored by this striker (where extra is None or No Ball - standard assumption simplified)
        # Actually in this app, runs column includes extras if Wide/NB is set.
        # Strict logic: runs where striker==player and extras!=Wide. 
        # But 'runs' value here includes '1' for wide?
        # Let's trust "runs" column for now but exclude Wides for ball count.
        p_balls = match_scores_df[
            (match_scores_df["striker"] == player_name) & 
            (~match_scores_df["extras"].isin(["Wide"]))
        ].shape[0]
        
        # For runs, we sum 'runs' column but subtract 1 if it was a Wide/NoBall? 
        # Actually our process_ball puts (1 + runs) into 'runs'. 
        # So if Wide+4, runs=5. 5 runs to team. 0 to batsman. 
        # If NoBall+4, runs=5. 1 extra, 4 batsman.
        # This data model is slightly simple. Let's approximate: 
        # Sum 'runs' for this striker. If Extra='Wide', runs=0 for him. 
        # If Extra='No Ball', runs = total - 1. 
        # Else runs = total.
        
        p_runs = 0
        p_df = match_scores_df[match_scores_df["striker"] == player_name]
        for _, row in p_df.iterrows():
            r = row['runs']
            ex = row['extras']
            if ex == 'Wide':
                r = 0 # Wides don't count and extra runs on wide usually don't go to bat unless overwrites.
                # In simple app: 0 to bat.
            elif ex == 'No Ball':
                r = r - 1 # 1 run is extra, rest is bat.
            p_runs += r
            
        if p_balls > 0:
            sr = (p_runs / p_balls) * 100
        else:
            sr = 0.0
            
        return p_runs, p_balls, sr

    s_runs, s_balls, s_sr = get_batter_stats(st.session_state[striker_key])
    ns_runs, ns_balls, ns_sr = get_batter_stats(st.session_state[nonstriker_key])

    # 2. Bowler Stats (Overs-Runs-Wickets)
    curr_bowler = st.session_state[bowler_key]
    if curr_bowler:
        b_df = match_scores_df[match_scores_df["bowler"] == curr_bowler]
        # Valid balls for overs: Not Wide, Not No Ball
        b_legal_balls = legal_balls(b_df).shape[0]
        b_overs = f"{b_legal_balls // 6}.{b_legal_balls % 6}"
        
        # Runs conceded: Sum runs. Exclude Byes/LegByes? YES.
        # If Bye/LegBye, runs count to team but not bowler.
        b_runs = b_df[~b_df["extras"].isin(["Bye", "Leg Bye"])]["runs"].sum()
        
        # Wickets: Yes, but exclude Run Out
        b_wickets = b_df[(b_df["wicket"] == "Yes") & (b_df["wicket_type"] != "Run Out")].shape[0]
        # Economy
        if float(b_overs) > 0:
             econ = b_runs / float(b_overs)
        else:
             econ = 0.0
    else:
        b_overs, b_runs, b_wickets, econ = "0.0", 0, 0, 0.0

    # Display Current Bowler & Batsmen
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Striker** 🏏")
        st.selectbox(
            "Striker",
            batting_team_players,
            key=striker_key,
            label_visibility="collapsed"
        )
        st.caption(f"🏏 {s_runs} ({s_balls}) | SR: {s_sr:.1f}")
    with col2:
        st.markdown(f"**Non-Striker** 🏃")
        nonstriker_options = [p for p in batting_team_players if p != st.session_state[striker_key]]
        current_non = st.session_state[nonstriker_key]
        idx = nonstriker_options.index(current_non) if current_non in nonstriker_options else 0
        st.selectbox(
            "Non-Striker",
            nonstriker_options,
            key=nonstriker_key,
            label_visibility="collapsed"
        )
        st.caption(f"🏏 {ns_runs} ({ns_balls}) | SR: {ns_sr:.1f}")
    with col3:
        st.markdown(f"**Bowler** ⚾")
        st.selectbox(
            "Bowler",
            bowling_team_players,
            key=bowler_key,
            label_visibility="collapsed"
        )
        st.caption(f"📊 {b_overs} - {b_runs} - {b_wickets} | Econ: {econ:.2f}")

    st.divider()

    # --- Button Based Scoring ---
    st.subheader("📝 Record Ball")

    # Initialize session state for ball processing if not exists
    if f"process_ball_{match_id}" not in st.session_state:
        st.session_state[f"process_ball_{match_id}"] = None
    
    # Initialize undo stack
    if f"undo_stack_{match_id}" not in st.session_state:
        st.session_state[f"undo_stack_{match_id}"] = []



    def process_ball(runs=0, extras="", wicket="", wicket_type="", out_player="", should_rerun=True, fielder="", runout_by=""):
        new_ball = {
            "match_id": match_id,
            "innings": current_innings,
            "over": current_balls // 6,
            "ball": current_balls % 6 + 1,
            "striker": st.session_state[striker_key],
            "non_striker": st.session_state[nonstriker_key],
            "bowler": st.session_state[bowler_key],
            "runs": runs,
            "extras": extras,
            "wicket": wicket,
            "wicket_type": wicket_type,
            "wicket_type": wicket_type,
            "fielder": fielder,
            "runout_by": runout_by,
            "batting_team": batting_team
        }
        
        # Save to CSV
        current_scores = load_csv(SCORES_CSV) # Reload to be safe
        updated_scores = pd.concat([current_scores, pd.DataFrame([new_ball])], ignore_index=True)
        updated_scores.to_csv(SCORES_CSV, index=False)
        
        # Logic for rotation/swapping
        # Logic for rotation/swapping
        if wicket == "Yes":
            # Set the out player to None to trigger new player selection
            if out_player == st.session_state[striker_key]:
                # Modified: Set flag instead of direct modification to avoid Widget Instantiated Error
                st.session_state[f"reset_{striker_key}"] = True
                
                # If run out (strikers crossed), might need to swap non-striker to striker end?
                # Simple logic for now: Just remove the out player.
            elif out_player == st.session_state[nonstriker_key]:
                st.session_state[f"reset_{nonstriker_key}"] = True
            
            # If odd runs were scored on a Run Out (e.g. 1 run then out), we might need to swap ends for the remaining batter?
            # Complexity: Ideally "who is on strike" depends on whether they crossed.
            # For "Bowled/Caught", runs=0 usually.
            # If Run Out and runs=1, they crossed.
            if runs % 2 != 0:
                 # Check if both are still assigned (one is None now), so we can't swap normally.
                 # We need to ensure the *remaining* player is at the correct end.
                 # If striker was out and runs=1, non-striker crossed -> becomes Striker?
                 # This logic is complex. Let's rely on User to select "New Striker" and "New Non-Striker" correctly in the UI prompt.
                 pass

        else:
             # Swap strikers on odd runs (if not boundary/extra that prevents swap)
            is_valid_ball = extras not in ["Wide", "No Ball"]
            if runs % 2 != 0:
                 st.session_state[striker_key], st.session_state[nonstriker_key] = \
                 st.session_state[nonstriker_key], st.session_state[striker_key]

        st.success(f"Recorded: {runs} runs {extras} {wicket}")
        if should_rerun:
            safe_rerun()

    # Scoring Grid
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    
    # Run Buttons
    # Use callbacks to prevent "Set after instantiation" error for striker swap
    if c1.button("0️⃣ Dot", on_click=process_ball, kwargs={"runs": 0, "should_rerun": False}): pass
    if c2.button("1️⃣ Single", on_click=process_ball, kwargs={"runs": 1, "should_rerun": False}): pass
    if c3.button("2️⃣ Double", on_click=process_ball, kwargs={"runs": 2, "should_rerun": False}): pass
    if c4.button("3️⃣ Three", on_click=process_ball, kwargs={"runs": 3, "should_rerun": False}): pass
    if c5.button("4️⃣ Four", on_click=process_ball, kwargs={"runs": 4, "should_rerun": False}): pass
    if c6.button("6️⃣ Six", on_click=process_ball, kwargs={"runs": 6, "should_rerun": False}): pass

    # Undo / Redo Controls
    u1, u2 = st.columns(2)
    if u1.button("↩️ Undo Last Ball"):
        scores_df = load_csv(SCORES_CSV)
        match_scores = scores_df[scores_df["match_id"] == match_id]
        if not match_scores.empty:
            last_idx = match_scores.index[-1]
            last_row = match_scores.loc[last_idx].to_dict()
            scores_df.drop(last_idx, inplace=True)
            scores_df.to_csv(SCORES_CSV, index=False)
            
            st.session_state[f"undo_stack_{match_id}"].append(last_row)
            st.toast("Last ball undone! ↩️")
            safe_rerun()
        else:
            st.warning("No balls to undo in this match.")

    if st.session_state[f"undo_stack_{match_id}"]:
        if u2.button("↪️ Redo"):
            last_undone = st.session_state[f"undo_stack_{match_id}"].pop()
            scores_df = load_csv(SCORES_CSV)
            scores_df = pd.concat([scores_df, pd.DataFrame([last_undone])], ignore_index=True)
            scores_df.to_csv(SCORES_CSV, index=False)
            st.toast("Redo successful! ↪️")
            safe_rerun()

    # Extras Handling - Multi-Step
    # 1. Select Extra Type
    # 2. Select Runs on that ball (e.g., Wide + 4 runs)
    
    st.markdown("### Extras & Wickets")
    e1, e2, e3, e4, w1 = st.columns(5)
    
    # State to toggle extra mode
    if f"extra_mode_{match_id}" not in st.session_state:
        st.session_state[f"extra_mode_{match_id}"] = None

    if e1.button("Wide", type="primary" if st.session_state[f"extra_mode_{match_id}"] == "Wide" else "secondary"):
        st.session_state[f"extra_mode_{match_id}"] = "Wide"
        safe_rerun()
    if e2.button("No Ball", type="primary" if st.session_state[f"extra_mode_{match_id}"] == "No Ball" else "secondary"):
        st.session_state[f"extra_mode_{match_id}"] = "No Ball"
        safe_rerun()
    if e3.button("Bye (1)", help="Add 1 Bye", on_click=process_ball, kwargs={"runs": 1, "extras": "Bye", "should_rerun": False}): pass
    if e4.button("Leg Bye (1)", help="Add 1 Leg Bye", on_click=process_ball, kwargs={"runs": 1, "extras": "Leg Bye", "should_rerun": False}): pass

    # If Wide or No Ball selected, show run options for that extra
    extra_mode = st.session_state[f"extra_mode_{match_id}"]
    if extra_mode in ["Wide", "No Ball"]:
        st.info(f"Select runs scored on this **{extra_mode}** (including the extra run? No, usually +1 is automatic. Input runs SCORED by batsman/overthrows).")
        st.markdown(f"**Adding: {extra_mode} + X runs**")
        
        ex_cols = st.columns(6)
        # Note: process_ball(runs) -> runs argument is TOTAL runs attributed to batsman/extras?
        # Logic: If Wide + 4 -> Total 5. 1 Wide Extra, 4 Wides? Or 1 Wide + 4 Runs?
        # Standard: 5 Wides. 
        # API: process_ball(runs=5, extras="Wide").
        # UI: User clicks "4". We send 5.
        
        def commit_extra(added_runs):
            total_runs = 1 + added_runs # 1 for the wide/NB itself
            process_ball(total_runs, extra_mode)
            st.session_state[f"extra_mode_{match_id}"] = None # Reset
            safe_rerun()

        if ex_cols[0].button(f"{extra_mode} + 0"): commit_extra(0)
        if ex_cols[1].button(f"{extra_mode} + 1"): commit_extra(1)
        if ex_cols[2].button(f"{extra_mode} + 2"): commit_extra(2)
        if ex_cols[3].button(f"{extra_mode} + 3"): commit_extra(3)
        if ex_cols[4].button(f"{extra_mode} + 4"): commit_extra(4)
        if ex_cols[5].button(f"{extra_mode} + 6"): commit_extra(6)
        
        if st.button("Cancel Extra"):
            st.session_state[f"extra_mode_{match_id}"] = None
            safe_rerun()

    # Wicket Handling
    if w1.button("☝️ OUT"):
        st.session_state[f"wicket_mode_{match_id}"] = True
    
    if st.session_state.get(f"wicket_mode_{match_id}", False):
        with st.form("wicket_form"):
            st.warning("Generaring Wicket...")
            w_type = st.selectbox("Dismissal Type", ["Bowled", "Caught", "Stumped", "Run Out", "LBW", "Other"])
            who_out = st.selectbox("Who is out?", [st.session_state[striker_key], st.session_state[nonstriker_key]])
            
            fielder_name = ""
            runout_thrower = ""
            
            if w_type == "Caught":
                 fielder_name = st.selectbox("Who took the catch?", bowling_team_players)
            elif w_type == "Stumped":
                 fielder_name = st.selectbox("Who stumped?", bowling_team_players, index=0) # Usually Keeper
            elif w_type == "Run Out":
                 runout_thrower = st.selectbox("Who threw the ball?", bowling_team_players)
            
            if st.form_submit_button("Confirm Wicket 🔴"):
                process_ball(0, "", "Yes", w_type, who_out, should_rerun=False, fielder=fielder_name, runout_by=runout_thrower)
                st.session_state[f"wicket_mode_{match_id}"] = False
                safe_rerun()

    # --- End of Over Summary (Field) ---
    if not match_scores_df.empty:
        curr_inn_df = match_scores_df[match_scores_df["innings"] == current_innings]
        if not curr_inn_df.empty:
            unique_overs = sorted(curr_inn_df["over"].unique())
            if unique_overs:
                last_ov = unique_overs[-1]
                ov_data = curr_inn_df[curr_inn_df["over"] == last_ov]
                
                runs_in_over = pd.to_numeric(ov_data["runs"], errors='coerce').sum()
                wkts_in_over = (ov_data["wicket"] == "Yes").sum()
                bowler = ov_data.iloc[-1]["bowler"] if not ov_data.empty else "?"
                
                st.info(f"📊 **End of Over {last_ov}**: **{int(runs_in_over)} Runs** | **{wkts_in_over} Wickets** | Bowler: **{bowler}**")

    # --- End of Over Logic (Next Bowler Selection) ---
    balls_faced_in_innings = legal_balls(
         scores[(scores["match_id"] == match_id) & (scores["innings"] == current_innings)]
    ).shape[0]

    if balls_faced_in_innings % 6 == 0 and balls_faced_in_innings != 0 and current_balls != 0:
         st.warning(f"END OF OVER {balls_faced_in_innings // 6} COMPLETE.")
         ack_key = f"ack_over_{match_id}_{balls_faced_in_innings}"
         
         if ack_key not in st.session_state:
             st.info("Select Next Bowler to continue:")
             
             def on_bowler_select():
                 st.session_state[bowler_key] = st.session_state[f"next_bowler_{match_id}_{balls_faced_in_innings}"]
                 st.session_state[striker_key], st.session_state[nonstriker_key] = \
                     st.session_state[nonstriker_key], st.session_state[striker_key]
                 st.session_state[ack_key] = True
             
             st.selectbox(
                 "Select Next Bowler", 
                 bowling_team_players, 
                 key=f"next_bowler_{match_id}_{balls_faced_in_innings}",
                 on_change=on_bowler_select
             )
             
             if st.button("Start Next Over ▶️"):
                 sel_b = st.session_state[f"next_bowler_{match_id}_{balls_faced_in_innings}"]
                 st.session_state[bowler_key] = sel_b
                 st.session_state[striker_key], st.session_state[nonstriker_key] = \
                     st.session_state[nonstriker_key], st.session_state[striker_key]
                 st.session_state[ack_key] = True
                 safe_rerun()
                 
             return # Halt execution


    # --- Commentary / Recent Events ---
    st.markdown("---")
    st.subheader("🎙 Commentary (Recent Balls)")
    
    # Reload scores to ensure latest
    comm_scores = load_csv(SCORES_CSV)
    if not comm_scores.empty:
        # Filter for this match
        comm_df = comm_scores[comm_scores["match_id"] == int(match_id)].copy()
        
        # Sort by latest
        comm_df = comm_df.sort_index(ascending=False).head(10)
        
        if not comm_df.empty:
            for _, row in comm_df.iterrows():
                # Format: 0.1 | Bowler to Striker | Runs [Extras] [Wicket]
                ov_str = f"{row['over']}.{row['ball']}"
                
                outcome = f"**{row['runs']}** runs"
                if pd.notna(row['extras']) and row['extras']:
                     outcome += f" ({row['extras']})"
                if row['wicket'] == "Yes":
                     w_type = row['wicket_type'] if pd.notna(row['wicket_type']) else "Wicket"
                     outcome += f" | 🔴 **OUT ({w_type})**"
                
                # Highlight boundaries
                if row['runs'] == 4: outcome += " 🟢 **FOUR**"
                if row['runs'] == 6: outcome += " 🟣 **SIX**"
                
                st.markdown(f"**{ov_str}** | {row['bowler']} to {row['striker']} | {outcome}")
                st.caption(f"Innings: {row['innings']}")
                st.divider()
        else:
            st.info("No balls recorded yet.")

    # (End of Over logic moved to top)

    # Handle New Striker Selection if someone is None (after wicket)
    # This logic runs on re-run
    current_striker = st.session_state.get(striker_key)
    current_non = st.session_state.get(nonstriker_key)
    
    if current_striker is None or current_non is None:
        st.error("🔴 Wicket Fell! Reorganize Batting.")
        st.info("Select who will be the Striker and Non-Striker now.")
        
        available = [p for p in batting_team_players] # All avail? Technically exclude out players.
        # Ideally exclude dismissed players. But reading 'scores' to filter out players is heavy.
        # User knows who is out.
        
        c1, c2 = st.columns(2)
        with c1:
            new_s = st.selectbox("New Striker", available, index=0, key=f"new_s_w_{match_id}_{current_balls}")
        with c2:
            new_ns = st.selectbox("New Non-Striker", available, index=1 if len(available)>1 else 0, key=f"new_ns_w_{match_id}_{current_balls}")
            
        if st.button("Resume Play ▶️"):
             st.session_state[striker_key] = new_s
             st.session_state[nonstriker_key] = new_ns
             safe_rerun()
        
        return # Stop execution until resolved

def fun():
    # uses your absolute path – keep as is if your data is here
    # uses your absolute path – keep as is if your data is here
    # df = pd.read_csv("/home/apiiit123/projects/major_project_2/sports_dashboard/data/cricket_scores.csv")
    df = pd.read_csv(SCORES_CSV)
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

    joblib.dump(regressor, "score_predictor.pkl")
    joblib.dump(classifier, "win_predictor.pkl")

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

    tournament_matches = matches[matches["tournament_id"] == tournament_id].reset_index(drop=True)
    if tournament_matches.empty:
        st.info("No scheduled matches for selected tournament.")
        return

    # Create proper options mapping Display Name -> Match ID
    match_options = {}
    for idx, row in tournament_matches.iterrows():
        t1 = teams.loc[teams["team_id"] == row["team1_id"], "team_name"].values[0] if not teams[teams["team_id"] == row["team1_id"]].empty else "Unknown"
        t2 = teams.loc[teams["team_id"] == row["team2_id"], "team_name"].values[0] if not teams[teams["team_id"] == row["team2_id"]].empty else "Unknown"
        label = f"Match {idx + 1}: {t1} vs {t2}"
        match_options[label] = row["match_id"]
        
    selected_label = st.selectbox("Select Match", list(match_options.keys()))
    match_id = match_options[selected_label]
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
        if df_team.empty:
             st.info("No data yet.")
             return

        df_team["Ball_no"] = (df_team["over"] * 6 + df_team["ball"]).astype(int)
        df_team["Dismissal"] = df_team["wicket"].apply(lambda x: 1 if x == "Yes" else 0)
        
        summary = df_team.groupby("striker").agg(
            {"runs": "sum", "Ball_no": "count", "Dismissal": "sum"}
        ).rename_axis(None).reset_index()
        
        # Ensure calculations are on numeric types
        runs = pd.to_numeric(summary["runs"], errors='coerce').fillna(0)
        balls = pd.to_numeric(summary["Ball_no"], errors='coerce').fillna(1) # avoid div0
        outs = pd.to_numeric(summary["Dismissal"], errors='coerce').fillna(0)
        
        summary["Strike Rate"] = round(runs / balls * 100, 2)
        summary["Average"] = round(runs / outs.replace(0, 1), 2)
        
        # Format
        summary.columns = ["Batter", "Runs", "Balls", "Outs", "Strike Rate", "Average"]
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
    if 'extras' in innings_df.columns:
        # Filter out Wide and No Ball (Case Sensitive check against stored values)
        # The app stores "Wide" and "No Ball" (Title Case)
        legal = innings_df[~innings_df['extras'].isin(['Wide', 'No Ball'])]
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

def compute_tournament_awards(tournament_id):
    # Load all matches for this tournament
    matches = load_csv(MATCHES_CSV)
    if matches.empty: return None
    
    t_matches = matches[matches["tournament_id"] == int(tournament_id)]
    if t_matches.empty: return None
    
    match_ids = t_matches["match_id"].tolist()
    
    scores = load_csv(SCORES_CSV)
    if scores.empty: return None
    
    # Filter scores for ANY match in this tournament
    df = scores[scores["match_id"].isin(match_ids)].copy()
    if df.empty: return None
    
    # --- Reuse Stats Logic (Aggregated) ---
    # Normalise
    df["runs"] = pd.to_numeric(df["runs"], errors="coerce").fillna(0).astype(int)
    
    # Batting
    bat = df.groupby("striker").agg(
        runs=("runs", "sum"),
        balls=("ball", "count")
    ).reset_index().rename(columns={"striker": "player_name"})
    bat["balls"] = bat["balls"].replace(0, 1)
    bat["strike_rate"] = (bat["runs"] / bat["balls"]) * 100
    
    # Bowling
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
    
    # Catches
    if "fielder" in df.columns:
        catches = df[df["fielder"] != ""]
        catches = catches.groupby("fielder")["fielder"].count().reset_index(name="catches")
        catches = catches.rename(columns={"fielder": "player_name"}) # Mapped from name directly in DB
    else:
        catches = pd.DataFrame(columns=["player_name", "catches"])
        
    # Merge
    stats = pd.merge(bat, bowl, how="outer", on="player_name")
    stats = pd.merge(stats, catches, how="outer", on="player_name").fillna(0)
    
    # Types
    for col in ["runs", "balls", "balls_bowled", "runs_conceded", "wickets", "catches"]:
        stats[col] = stats[col].astype(int)
    for col in ["strike_rate", "economy"]:
        stats[col] = pd.to_numeric(stats[col], errors="coerce").fillna(0.0)
        
    # MVP
    stats["strike_rate_factor"] = (stats["strike_rate"] - 100.0) / 5.0
    stats["economy_factor"] = (stats["economy"] - 6.0) * 2.0
    stats["mvp_score"] = (
        stats["runs"] * 1.2 +
        stats["wickets"] * 15 +
        stats["catches"] * 8 +
        stats["strike_rate_factor"] -
        stats["economy_factor"]
    )
    
    # Sort by MVP
    leaderboard = stats.sort_values("mvp_score", ascending=False).reset_index(drop=True)
    return leaderboard

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

