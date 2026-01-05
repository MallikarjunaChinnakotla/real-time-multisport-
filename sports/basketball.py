import streamlit as st
import pandas as pd
import os
from datetime import datetime

BASKETBALL_FOLDER = "sports_dashboard/data"
TOURNAMENTS_CSV = os.path.join(BASKETBALL_FOLDER, "basketball_tournaments.csv")
TEAMS_CSV = os.path.join(BASKETBALL_FOLDER, "basketball_teams.csv")
PLAYERS_CSV = os.path.join(BASKETBALL_FOLDER, "basketball_players.csv")
MATCHES_CSV = os.path.join(BASKETBALL_FOLDER, "basketball_matches.csv")
SCORES_CSV = os.path.join(BASKETBALL_FOLDER, "basketball_scores.csv")



# --------- Utility Functions ----------
def load_csv(filename, columns=None):
    """Load CSV file or return empty DataFrame with given columns.
       Ensures that all expected columns exist, even in old files."""
    path = os.path.join(BASKETBALL_FOLDER, filename)
    if os.path.exists(path):
        df = pd.read_csv(path)
        if columns:
            for col in columns:
                if col not in df.columns:
                    df[col] = None  # add missing columns if not present
        return df
    else:
        return pd.DataFrame(columns=columns) if columns else pd.DataFrame()

def save_csv(df, filename):
    """Save DataFrame to CSV file."""
    os.makedirs(BASKETBALL_FOLDER, exist_ok=True)
    df.to_csv(os.path.join(BASKETBALL_FOLDER, filename), index=False)
def view_tournaments():
    st.subheader("📋 View Tournaments")
    tournaments = load_csv("basketball_tournaments.csv")
    matches = load_csv("basketball_matches.csv")
    teams = load_csv("basketball_teams.csv")
    
    if tournaments.empty:
        st.warning("No tournaments found.")
        return

    # Select tournament
    tournament_names = tournaments["tournament_name"].tolist()
    selected_tournament = st.selectbox("Select Tournament", tournament_names)

    if selected_tournament:
        st.markdown(f"### Matches in {selected_tournament}")

        # Get tournament_id for selected tournament
        tournament_id = tournaments.loc[tournaments["tournament_name"] == selected_tournament, "tournament_id"].values[0]

        # Filter matches for this tournament
        tournament_matches = matches[matches["tournament_id"] == tournament_id]

        if tournament_matches.empty:
            st.info("No matches scheduled for this tournament yet.")
        else:
            # Define function to get team name from team_id
            def get_team_name(team_id):
                name = teams.loc[teams["team_id"] == team_id, "team_name"]
                return name.values[0] if not name.empty else "Unknown"

            # Assuming matches have 'team1_id' and 'team2_id' columns storing team IDs
            display_df = tournament_matches.copy()

            # Map team IDs to names
            if "team1_id" in display_df.columns and "team2_id" in display_df.columns:
                display_df["Team 1"] = display_df["team1_id"].apply(get_team_name)
                display_df["Team 2"] = display_df["team2_id"].apply(get_team_name)
            else:
                # If your matches CSV uses 'team1' and 'team2' as team names directly
                display_df["Team 1"] = display_df.get("team1", "Unknown")
                display_df["Team 2"] = display_df.get("team2", "Unknown")

            display_df["Match Date"] = display_df["match_date"]
            display_df["Venue"] = display_df["venue"]

            st.dataframe(display_df[["match_id", "Team 1", "Team 2", "Match Date", "Venue"]].reset_index(drop=True))


# --------- Add Tournament ----------
def add_tournament():
    st.subheader("🏆 Add Basketball Tournament")
    tournament_name = st.text_input("Tournament Name")
    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")
    location = st.text_input("Location")

    if st.button("Add Tournament"):
        df = load_csv("basketball_tournaments.csv", 
                      ["tournament_id", "tournament_name", "start_date", "end_date", "location"])
        tournament_id = len(df) + 1
        new_row = pd.DataFrame([[tournament_id, tournament_name, start_date, end_date, location]],
                               columns=df.columns)
        df = pd.concat([df, new_row], ignore_index=True)
        save_csv(df, "basketball_tournaments.csv")
        st.success(f"Tournament '{tournament_name}' added successfully!")

# --------- Add Team ----------
def add_team():
    st.subheader("🏀 Add Basketball Team")
    tournaments = load_csv("basketball_tournaments.csv", 
                            ["tournament_id", "tournament_name", "start_date", "end_date", "location"])
    if tournaments.empty:
        st.warning("No tournaments found. Please add a tournament first.")
        return

    tournament_choice = st.selectbox("Select Tournament", tournaments["tournament_name"])
    tournament_id = tournaments.loc[tournaments["tournament_name"] == tournament_choice, "tournament_id"].values[0]
    team_name = st.text_input("Team Name")

    if st.button("Add Team"):
        df = load_csv("basketball_teams.csv", ["team_id", "team_name", "tournament_id"])
        team_id = len(df) + 1
        new_row = pd.DataFrame([[team_id, team_name, tournament_id]], columns=df.columns)
        df = pd.concat([df, new_row], ignore_index=True)
        save_csv(df, "basketball_teams.csv")
        st.success(f"Team '{team_name}' added successfully!")

# --------- Add Player ----------
def add_player():
    st.subheader("👤 Add Basketball Player")
    teams = load_csv("basketball_teams.csv", ["team_id", "team_name", "tournament_id"])
    if teams.empty:
        st.warning("No teams found. Please add a team first.")
        return

    team_choice = st.selectbox("Select Team", teams["team_name"])
    team_id = teams.loc[teams["team_name"] == team_choice, "team_id"].values[0]
    player_name = st.text_input("Player Name")

    if st.button("Add Player"):
        df = load_csv("basketball_players.csv", ["player_id", "player_name", "team_id"])
        player_id = len(df) + 1
        new_row = pd.DataFrame([[player_id, player_name, team_id]], columns=df.columns)
        df = pd.concat([df, new_row], ignore_index=True)
        save_csv(df, "basketball_players.csv")
        st.success(f"Player '{player_name}' added successfully!")

# --------- Schedule Match ----------
def schedule_match():
    st.subheader("📅 Schedule Basketball Match")
    tournaments = load_csv("basketball_tournaments.csv", 
                            ["tournament_id", "tournament_name", "start_date", "end_date", "location"])
    teams = load_csv("basketball_teams.csv", ["team_id", "team_name", "tournament_id"])

    if tournaments.empty or teams.empty:
        st.warning("Please add tournaments and teams first.")
        return

    tournament_choice = st.selectbox("Select Tournament", tournaments["tournament_name"])
    tournament_id = tournaments.loc[tournaments["tournament_name"] == tournament_choice, "tournament_id"].values[0]

    eligible_teams = teams[teams["tournament_id"] == tournament_id]
    if len(eligible_teams) < 2:
        st.warning("Need at least 2 teams in the tournament.")
        return

    team1 = st.selectbox("Team 1", eligible_teams["team_name"])
    team2 = st.selectbox("Team 2", [t for t in eligible_teams["team_name"] if t != team1])
    match_date = st.date_input("Match Date")
    venue = st.text_input("Venue")

    if st.button("Schedule Match"):
        df = load_csv("basketball_matches.csv", 
                      ["match_id", "tournament_id", "team1_id", "team2_id", "match_date", "venue"])
        match_id = len(df) + 1
        team1_id = eligible_teams.loc[eligible_teams["team_name"] == team1, "team_id"].values[0]
        team2_id = eligible_teams.loc[eligible_teams["team_name"] == team2, "team_id"].values[0]
        new_row = pd.DataFrame([[match_id, tournament_id, team1_id, team2_id, match_date, venue]], columns=df.columns)
        df = pd.concat([df, new_row], ignore_index=True)
        save_csv(df, "basketball_matches.csv")
        st.success(f"Match scheduled successfully! Match ID: {match_id}")

# --------- Update Live Score ----------
def update_score():
    st.subheader("🏀 Update Live Score")
    
    matches = load_csv("basketball_matches.csv", 
                       ["match_id", "tournament_id", "team1_id", "team2_id", "match_date", "venue"])
    players = load_csv("basketball_players.csv", ["player_id", "player_name", "team_id"])
    teams = load_csv("basketball_teams.csv", ["team_id", "team_name", "tournament_id"])

    if matches.empty:
        st.warning("No matches available.")
        return

    match_id = st.selectbox("Select Match", matches["match_id"])
    match_data = matches[matches["match_id"] == match_id].iloc[0]

    team1_id = match_data["team1_id"]
    team2_id = match_data["team2_id"]

    team1_name = teams.loc[teams["team_id"] == team1_id, "team_name"].values[0]
    team2_name = teams.loc[teams["team_id"] == team2_id, "team_name"].values[0]

    # --- Live Scoreboard Display ---
    score_df = load_csv("basketball_scores.csv", 
                        ["match_id", "quarter", "minute", "event_type", "player_id", "team_id", "points"])
    match_scores = score_df[score_df["match_id"] == match_id]
    score_team1 = match_scores[match_scores["team_id"] == team1_id]["points"].sum()
    score_team2 = match_scores[match_scores["team_id"] == team2_id]["points"].sum()

    st.markdown(
        f"<h3 style='text-align:center;'>{team1_name} <span style='color:green'>{score_team1}</span> - "
        f"<span style='color:red'>{score_team2}</span> {team2_name}</h3>",
        unsafe_allow_html=True
    )

    st.divider()  # Just to separate scoreboard from form

    # --- Event Form ---
    quarter = st.selectbox("Quarter", ["Q1", "Q2", "Q3", "Q4"])
    minute = st.number_input("Minute", min_value=0, max_value=48, step=1)
    event_type = st.selectbox("Event Type", ["Points", "Foul", "Rebound", "Assist", "Substitution"])

    team_choice = st.selectbox("Team", [team1_name, team2_name])
    team_id = team1_id if team_choice == team1_name else team2_id

    player_choice = st.selectbox("Player", players[players["team_id"] == team_id]["player_name"])
    player_id = players.loc[players["player_name"] == player_choice, "player_id"].values[0]

    points = 0
    if event_type == "Points":
        points = st.selectbox("Points Scored", [1, 2, 3])

    if st.button("Save Event"):
        df = load_csv("basketball_scores.csv", 
                      ["match_id", "quarter", "minute", "event_type", "player_id", "team_id", "points"])
        new_row = pd.DataFrame([[match_id, quarter, minute, event_type, player_id, team_id, points]], columns=df.columns)
        df = pd.concat([df, new_row], ignore_index=True)
        save_csv(df, "basketball_scores.csv")
        st.success("Event recorded successfully!")


# --------- View Match Summary ----------
def view_summary():
    import altair as alt

    st.subheader("📊 Match Summary")
    match_id = st.number_input("Enter Match ID", min_value=1, step=1)

    # Load data with correct columns
    scores = load_csv("basketball_scores.csv", 
                      ["match_id", "quarter", "minute", "event_type", "player_id", "team_id", "points"])
    players = load_csv("basketball_players.csv", ["player_id", "player_name", "team_id"])
    teams = load_csv("basketball_teams.csv", ["team_id", "team_name", "tournament_id"])

    match_scores = scores[scores["match_id"] == match_id]
    if match_scores.empty:
        st.warning("No events found for this match.")
        return

    # ---- Points by Team ----
    points_by_team = match_scores.groupby("team_id")["points"].sum()
    points_by_team.index = points_by_team.index.map(
        lambda tid: teams.loc[teams["team_id"] == tid, "team_name"].values[0]
        if tid in teams["team_id"].values else "Unknown"
    )

    # Convert to DataFrame for Altair
    df_points = points_by_team.reset_index()
    df_points.columns = ["Team", "Points"]

    chart = (
        alt.Chart(df_points)
        .mark_bar()
        .encode(
            x=alt.X("Team", sort=None, title="Team"),
            y=alt.Y("Points", title="Total Points"),
            tooltip=["Team", "Points"]
        )
        .properties(width=400, height=300)  # Reduced width
    )
    st.altair_chart(chart, use_container_width=False)

def run():
    st.title("🏀 badsketball Dashboard")
    st.write("Live basketball stats go here...")
# --------- Main Basketball Menu ----------
def run_basketball():
    st.sidebar.title("🏀 Basketball Module")
    choice = st.sidebar.radio(
        "Select Function",
        (
            "Add Tournament",
            "Add Team",
            "Add Player",
            "View Tournaments",
            "Schedule Match",
            "Update Live Score",
            "View Match Summary"
        )
    )

    if choice == "Add Tournament":
        add_tournament()
    elif choice == "Add Team":
        add_team()
    elif choice == "Add Player":
        add_player()
    elif choice == "View Tournaments":
        view_tournaments()
    elif choice == "Schedule Match":
        schedule_match()
    elif choice == "Update Live Score":
        update_score()
    elif choice == "View Match Summary":
        view_summary()

