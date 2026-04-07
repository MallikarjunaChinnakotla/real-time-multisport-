import streamlit as st
import pandas as pd
import os
import time
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
            
            st.divider()
            st.subheader("🏆 Tournament Stats")
            if st.button("📊 Show MVP & Leaderboard"):
                scores_df = load_csv("basketball_scores.csv", ["match_id", "quarter", "team_id", "player_id", "points", "timestamp"])
                players_df = load_csv("basketball_players.csv", ["player_id", "player_name", "team_id"])
                
                mid_list = tournament_matches["match_id"].tolist()
                t_scores = scores_df[scores_df["match_id"].isin(mid_list)].copy()
                
                if t_scores.empty:
                    st.warning("No stats available.")
                else:
                    t_scores["points"] = pd.to_numeric(t_scores["points"], errors='coerce').fillna(0).astype(int)
                    # FIX: Cast player_id to int to match players_df
                    t_scores["player_id"] = pd.to_numeric(t_scores["player_id"], errors='coerce').fillna(0).astype(int)
                    players_df["player_id"] = pd.to_numeric(players_df["player_id"], errors='coerce').fillna(0).astype(int)
                    
                    agg = t_scores.groupby("player_id")["points"].sum().reset_index()
                    agg = pd.merge(agg, players_df, on="player_id", how="left")
                    agg["player_name"] = agg["player_name"].fillna("Unknown")
                    
                    leaderboard = agg.sort_values("points", ascending=False).head(10)
                    
                    if not leaderboard.empty:
                        top = leaderboard.iloc[0]
                        # Image logic
                        def get_img(row):
                            default_img = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
                            if "profile_image" in row and pd.notna(row["profile_image"]) and row["profile_image"]:
                                if os.path.exists(row["profile_image"]):
                                    return row["profile_image"]
                            return default_img
                        mvp_img = get_img(top)

                        c1, c2 = st.columns([1, 2])
                        with c1:
                            st.markdown("### 🏅 MVP (Most Points)")
                            st.image(mvp_img, width=150)
                        with c2:
                            st.markdown(f"## **{top['player_name']}**")
                            st.markdown(f"**Points: {top['points']}**")
                            
                        st.dataframe(leaderboard[["player_name", "points", "team_id"]])
                    else:
                        st.info("No player points recorded.")


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
    phone_number = st.text_input("Player Phone Number")
    uploaded_file = st.file_uploader("Upload Player Photo", type=['jpg', 'jpeg', 'png'])

    if st.button("Add Player"):
        df = load_csv("basketball_players.csv", ["player_id", "player_name", "team_id", "phone_number", "profile_image"])
        player_id = len(df) + 1
        
        # Check/Create columns
        if "phone_number" not in df.columns:
             df["phone_number"] = ""
        if "profile_image" not in df.columns:
             df["profile_image"] = ""
             
        image_path = ""
        if uploaded_file is not None:
            img_dir = os.path.join(BASKETBALL_FOLDER, "player_images")
            os.makedirs(img_dir, exist_ok=True)
            
            timestamp = int(datetime.now().timestamp())
            safe_name = "".join(x for x in player_name if x.isalnum())
            ext = uploaded_file.name.split('.')[-1]
            filename = f"{player_id}_{safe_name}_{timestamp}.{ext}"
            save_path = os.path.join(img_dir, filename)
            
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            image_path = save_path
             
        new_row = pd.DataFrame([[player_id, player_name, team_id, str(phone_number), image_path]], columns=["player_id", "player_name", "team_id", "phone_number", "profile_image"])
        df = pd.concat([df, new_row], ignore_index=True)
        save_csv(df, "basketball_players.csv")
        st.success(f"Player '{player_name}' added successfully!")
        if image_path:
            st.image(image_path, width=150, caption="Uploaded Photo")

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
    
    tournaments = load_csv("basketball_tournaments.csv", 
                        ["tournament_id", "tournament_name", "start_date", "end_date", "location"])
    matches = load_csv("basketball_matches.csv", 
                       ["match_id", "tournament_id", "team1_id", "team2_id", "match_date", "venue"])
    players = load_csv("basketball_players.csv", ["player_id", "player_name", "team_id"])
    teams = load_csv("basketball_teams.csv", ["team_id", "team_name", "tournament_id"])

    if matches.empty:
        st.warning("No matches available.")
        return

    # 1. Select Tournament
    tournament_names = tournaments["tournament_name"].tolist()
    if not tournament_names:
        st.warning("No tournaments found.")
        return
        
    selected_tourney_name = st.selectbox("Select Tournament", tournament_names)
    selected_tourney_id = tournaments.loc[tournaments["tournament_name"] == selected_tourney_name, "tournament_id"].values[0]

    # 2. Filter Matches
    tourney_matches = matches[matches["tournament_id"] == selected_tourney_id]
    
    if tourney_matches.empty:
        st.info("No matches found for this tournament.")
        return

    # Helper to get team name
    def get_team_name(tid):
        name = teams.loc[teams["team_id"] == tid, "team_name"]
        return name.values[0] if not name.empty else f"Team {tid}"

    # Create friendly match labels
    match_options = {}
    for _, row in tourney_matches.iterrows():
        mid = row["match_id"]
        t1 = get_team_name(row["team1_id"])
        t2 = get_team_name(row["team2_id"])
        date = row["match_date"]
        label = f"Match #{mid}: {t1} vs {t2} ({date})"
        match_options[label] = mid

    selected_match_label = st.selectbox("Select Match", list(match_options.keys()))
    match_id = match_options[selected_match_label]
    match_data = tourney_matches[tourney_matches["match_id"] == match_id].iloc[0]

    team1_id = match_data["team1_id"]
    team2_id = match_data["team2_id"]

    team1_name = get_team_name(team1_id)
    team2_name = get_team_name(team2_id)

    # --- Live Match Timer ---
    if "bb_timer_start" not in st.session_state:
        st.session_state["bb_timer_start"] = None
    if "bb_timer_paused" not in st.session_state:
        st.session_state["bb_timer_paused"] = False
    if "bb_timer_elapsed" not in st.session_state:
        st.session_state["bb_timer_elapsed"] = 0.0

    st.markdown("### ⏱ Match Timer")
    t1, t2, t3 = st.columns(3)
    if t1.button("▶ Start/Resume"):
        if st.session_state["bb_timer_start"] is None:
            st.session_state["bb_timer_start"] = time.time()
        elif st.session_state["bb_timer_paused"]:
            # Adjust start time to account for pause duration
            now = time.time()
            # logic: new_start = now - previously_elapsed
            st.session_state["bb_timer_start"] = now - st.session_state["bb_timer_elapsed"]
            st.session_state["bb_timer_paused"] = False

    if t2.button("⏸ Pause"):
        if st.session_state["bb_timer_start"] is not None and not st.session_state["bb_timer_paused"]:
            st.session_state["bb_timer_elapsed"] = time.time() - st.session_state["bb_timer_start"]
            st.session_state["bb_timer_paused"] = True

    if t3.button("🔄 Reset"):
        st.session_state["bb_timer_start"] = None
        st.session_state["bb_timer_paused"] = False
        st.session_state["bb_timer_elapsed"] = 0.0

    # Calculate Display Time (Countdown)
    QUARTER_DURATION = 10 * 60 # 10 minutes
    
    current_elapsed = 0.0
    if st.session_state["bb_timer_start"] is not None:
        if st.session_state["bb_timer_paused"]:
            current_elapsed = st.session_state["bb_timer_elapsed"]
        else:
            current_elapsed = time.time() - st.session_state["bb_timer_start"]
    
    # Countdown Logic
    remaining_seconds = max(0, QUARTER_DURATION - current_elapsed)
    
    mins = int(remaining_seconds // 60)
    secs = int(remaining_seconds % 60)
    
    # Auto-detect Quarter (Cycle based on total resets? Or just manual)
    # For countdown, auto-detect is harder unless we track total match time.
    # We'll rely on manual Quarter selection or keep simple Q detection if users generally reset per quarter.
    # For now, let's just show the Countdown.
    
    st.markdown(f"## **{mins:02d}:{secs:02d}** (Countdown)")
    
    # Auto-refresh if timer is running and not finished
    if st.session_state["bb_timer_start"] is not None and not st.session_state["bb_timer_paused"] and remaining_seconds > 0:
        time.sleep(1)
        st.rerun()

    # --- Live Scoreboard ---
    score_df = load_csv("basketball_scores.csv", 
                        ["match_id", "quarter", "minute", "event_type", "player_id", "team_id", "points"])
    match_scores = score_df[score_df["match_id"] == match_id]
    
    # Calculate scores
    s1 = match_scores[match_scores["team_id"] == team1_id]["points"].sum()
    s2 = match_scores[match_scores["team_id"] == team2_id]["points"].sum()
    
    st.markdown(
        f"<h1 style='text-align:center; color: #4CAF50;'>{team1_name} {s1} - {s2} {team2_name}</h1>", 
        unsafe_allow_html=True
    )
    
    # Quarter Breakdown Display
    q_scores = match_scores.groupby(["quarter", "team_id"])["points"].sum().unstack(fill_value=0)
    # Ensure all quarters exist in view
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        if q not in q_scores.index:
            q_scores.loc[q] = 0
    q_scores = q_scores.fillna(0).astype(int)

    st.markdown("#### Quarter Breakdown")
    # Simple standardized table
    q_display = pd.DataFrame({
        team1_name: [q_scores.loc[q, team1_id] if team1_id in q_scores.columns else 0 for q in ["Q1","Q2","Q3","Q4"]],
        team2_name: [q_scores.loc[q, team2_id] if team2_id in q_scores.columns else 0 for q in ["Q1","Q2","Q3","Q4"]]
    }, index=["Q1", "Q2", "Q3", "Q4"]).T
    st.dataframe(q_display)

    st.divider()

    # --- Button-Based Scoring Flow ---
    if "bb_step" not in st.session_state:
        st.session_state["bb_step"] = "SELECT_EVENT" 
    if "bb_event_type" not in st.session_state:
        st.session_state["bb_event_type"] = None
    if "bb_points" not in st.session_state:
        st.session_state["bb_points"] = 0

    def reset_bb_flow():
        st.session_state["bb_step"] = "SELECT_EVENT"
        st.session_state["bb_event_type"] = None
        st.session_state["bb_points"] = 0

    def safe_rerun():
        try:
            st.rerun()
        except AttributeError:
            st.experimental_rerun()

    if st.button("❌ Reset Form"):
        reset_bb_flow()
        safe_rerun()

    # STEP 1: Select Points / Event
    if st.session_state["bb_step"] == "SELECT_EVENT":
        st.markdown("#### Select Score / Event")
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("🏀 1 Point (FT)", use_container_width=True):
            st.session_state["bb_event_type"] = "Points"
            st.session_state["bb_points"] = 1
            st.session_state["bb_step"] = "DETAILS"
            safe_rerun()
        if c2.button("🏀 2 Points", use_container_width=True):
            st.session_state["bb_event_type"] = "Points"
            st.session_state["bb_points"] = 2
            st.session_state["bb_step"] = "DETAILS"
            safe_rerun()
        if c3.button("🏀 3 Points", use_container_width=True):
            st.session_state["bb_event_type"] = "Points"
            st.session_state["bb_points"] = 3
            st.session_state["bb_step"] = "DETAILS"
            safe_rerun()
        
        c5, c6 = st.columns(2)
        if c5.button("🚫 Foul", use_container_width=True):
             st.session_state["bb_event_type"] = "Foul"
             st.session_state["bb_points"] = 0
             st.session_state["bb_step"] = "DETAILS"
             safe_rerun()
        if c6.button("🔄 Other (Sub/Timeout)", use_container_width=True):
             st.session_state["bb_event_type"] = "Other"
             st.session_state["bb_points"] = 0
             st.session_state["bb_step"] = "DETAILS"
             safe_rerun()

    # STEP 2: Details
    if st.session_state["bb_step"] == "DETAILS":
        evt_type = st.session_state["bb_event_type"]
        pts = st.session_state["bb_points"]
        
        st.info(f"Recording: **{evt_type}** ({pts} pts)")
        
        with st.form("bb_details_form"):
            col_t, col_p = st.columns(2)
            
            # Select Team
            with col_t:
                team_choice = st.selectbox("Select Team", [team1_name, team2_name])
                selected_team_id = team1_id if team_choice == team1_name else team2_id
            
            # Select Player
            with col_p:
                team_players_list = players[players["team_id"] == selected_team_id]["player_name"].tolist()
                player_choice = st.selectbox("Select Player", team_players_list if team_players_list else ["Unknown"])
            
            # Metadata
            quarter = st.selectbox("Quarter", ["Q1", "Q2", "Q3", "Q4"])
            
            # Auto-fill minute from timer (Elapsed = Duration - Remaining)
            # Minute 0 = 10:00 to 9:00 remaining
            elapsed_min = int((QUARTER_DURATION - remaining_seconds) // 60)
            quarter_val = st.number_input("Minute", 0, 10, elapsed_min)
            
            if st.form_submit_button("✅ Confirm"):
                # Save Logic
                df = load_csv("basketball_scores.csv", 
                              ["match_id", "quarter", "minute", "event_type", "player_id", "team_id", "points"])
                
                pid = players.loc[(players["player_name"] == player_choice) & (players["team_id"] == selected_team_id), "player_id"]
                pid = pid.values[0] if not pid.empty else ""
                
                new_row = pd.DataFrame([[
                    match_id, 
                    quarter, 
                    quarter_val, 
                    evt_type if evt_type != "Other" else "Other", 
                    pid, 
                    selected_team_id, 
                    pts
                ]], columns=df.columns)
                
                df = pd.concat([df, new_row], ignore_index=True)
                save_csv(df, "basketball_scores.csv")
                
                st.success("Saved!")
                reset_bb_flow()
                safe_rerun()


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

