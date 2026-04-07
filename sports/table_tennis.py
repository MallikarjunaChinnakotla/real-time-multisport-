# table_tennis.py
import os
import pandas as pd
import streamlit as st
from datetime import datetime

DATA_DIR = "sports_dashboard/data"
os.makedirs(DATA_DIR, exist_ok=True)

T_CSV = os.path.join(DATA_DIR, "tt_tournaments.csv")
TEAM_CSV = os.path.join(DATA_DIR, "tt_teams.csv")
PLAYER_CSV = os.path.join(DATA_DIR, "tt_players.csv")
MATCH_CSV = os.path.join(DATA_DIR, "tt_matches.csv")
SCORE_CSV = os.path.join(DATA_DIR, "tt_scores.csv")

# CSV HEADERS
T_HDR = ["tournament_id", "tournament_name", "start_date", "end_date", "location"]
TEAM_HDR = ["team_id", "team_name", "tournament_id"]
PLAYER_HDR = ["player_id", "player_name", "team_id"]
MATCH_HDR = ["match_id", "tournament_id", "team1_id", "team2_id", "match_date", "venue", "format"]
SCORE_HDR = ["match_id", "set_no", "team_id", "points", "timestamp"]


def init_files():
    for f, h in [(T_CSV, T_HDR),(TEAM_CSV, TEAM_HDR),(PLAYER_CSV, PLAYER_HDR),
                 (MATCH_CSV, MATCH_HDR),(SCORE_CSV, SCORE_HDR)]:
        if not os.path.exists(f):
            pd.DataFrame(columns=h).to_csv(f, index=False)


def load_csv(p, h): return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame(columns=h)
def save_csv(df, p): df.to_csv(p, index=False)

init_files()

def add_tournament():
    st.subheader("🏆 Add Tournament")
    df = load_csv(T_CSV, T_HDR)
    name = st.text_input("Tournament Name")
    loc = st.text_input("Location")
    s = st.date_input("Start")
    e = st.date_input("End")

    if st.button("ADD"):
        new_id = df["tournament_id"].max()+1 if not df.empty else 1
        df.loc[len(df)] = [new_id, name, s, e, loc]
        save_csv(df, T_CSV)
        st.success("Tournament Added!")

def add_team():
    st.subheader("➕ Add Team")
    df = load_csv(TEAM_CSV, TEAM_HDR)
    tours = load_csv(T_CSV, T_HDR)
    if tours.empty: return st.warning("Add a tournament first")

    team = st.text_input("Team Name")
    tour = st.selectbox("Tournament", tours["tournament_name"])

    tid = tours.loc[tours["tournament_name"]==tour,"tournament_id"].values[0]
    if st.button("Save Team"):
        new_id = df["team_id"].max()+1 if not df.empty else 1
        df.loc[len(df)] = [new_id, team, tid]
        save_csv(df, TEAM_CSV)
        st.success("Team added")


def add_player():
    st.subheader("➕ Add Player")
    df = load_csv(PLAYER_CSV, PLAYER_HDR)
    teams = load_csv(TEAM_CSV, TEAM_HDR)
    if teams.empty: return st.warning("Add teams first")

    p = st.text_input("Player Name")
    phone = st.text_input("Player Phone Number")
    tm = st.selectbox("Team", teams["team_name"])
    tid = teams.loc[teams["team_name"]==tm,"team_id"].values[0]

    if st.button("Save Player"):
        pid = df["player_id"].max()+1 if not df.empty else 1
        
        if "phone_number" not in df.columns:
            df["phone_number"] = ""
            
        new_row = pd.DataFrame([[pid,p,tid, str(phone)]], columns=["player_id","player_name","team_id","phone_number"])
        df = pd.concat([df, new_row], ignore_index=True)
        save_csv(df, PLAYER_CSV)
        st.success("Player added!")

def schedule_match():
    st.subheader("📅 Schedule Match")
    df = load_csv(MATCH_CSV, MATCH_HDR)
    teams = load_csv(TEAM_CSV, TEAM_HDR)
    tours = load_csv(T_CSV, T_HDR)
    if tours.empty or teams.empty: return st.warning("Add teams+tournaments first")

    tour = st.selectbox("Tournament", tours["tournament_name"])
    tid = tours.loc[tours["tournament_name"]==tour,"tournament_id"].values[0]

    valid = teams[teams["tournament_id"]==tid]
    if len(valid)<2: return st.error("Need 2+ teams")

    t1 = st.selectbox("Team 1", valid["team_name"])
    t2 = st.selectbox("Team 2", [x for x in valid["team_name"] if x!=t1])

    fmt = st.radio("Match Format",["Single Set (21)","Best of 3 (11 per set)"])
    d = st.date_input("Match Date")
    venue = st.text_input("Venue")

    if st.button("Schedule"):
        mid = df["match_id"].max()+1 if not df.empty else 1
        df.loc[len(df)] = [mid,tid,
                           valid.loc[valid["team_name"]==t1,"team_id"].values[0],
                           valid.loc[valid["team_name"]==t2,"team_id"].values[0],
                           d,venue,fmt]
        save_csv(df, MATCH_CSV)
        st.success("Match scheduled!")

def update_live():
    st.subheader("🏓 Live Scoring")
    matches = load_csv(MATCH_CSV, MATCH_HDR)
    if matches.empty: return st.warning("No matches")

    tours = load_csv(T_CSV, T_HDR)
    if tours.empty:
        st.warning("No tournaments found")
        return

    # 1. Select Tournament
    t_names = tours["tournament_name"].tolist()
    sel_tour = st.selectbox("Select Tournament", t_names)
    tid = tours.loc[tours["tournament_name"]==sel_tour,"tournament_id"].values[0]

    # 2. Filter matches
    t_matches = matches[matches["tournament_id"] == tid].copy()
    if t_matches.empty:
        st.info("No matches in this tournament")
        return

    # 3. Match Selection (Local Numbering)
    t_matches = t_matches.sort_values("match_id")
    t_matches["local_id"] = range(1, len(t_matches)+1)

    teams = load_csv(TEAM_CSV, TEAM_HDR)
    def get_tn(tid):
        r = teams[teams["team_id"]==tid]
        return r.iloc[0]["team_name"] if not r.empty else "Unknown"

    match_opts = {}
    for _, r in t_matches.iterrows():
        mid_val = r["match_id"]
        lid = r["local_id"]
        t1 = get_tn(r["team1_id"])
        t2 = get_tn(r["team2_id"])
        lbl = f"Match #{lid}: {t1} vs {t2} ({r['match_date']})"
        match_opts[lbl] = mid_val

    sel_lbl = st.selectbox("Select Match", list(match_opts.keys()))
    m = match_opts[sel_lbl]
    match = matches[matches["match_id"]==m].iloc[0]

    teams = load_csv(TEAM_CSV, TEAM_HDR)
    team1 = teams.loc[teams["team_id"]==match["team1_id"],"team_name"].values[0]
    team2 = teams.loc[teams["team_id"]==match["team2_id"],"team_name"].values[0]

    fmt = match["format"]
    max_sets = 1 if "Single" in fmt else 3
    max_points = 21 if "Single" in fmt else 11

    st.write(f"### Format: {fmt} | Target: {max_points} points per set")

    # --- Live Scoreboard ---
    score_df = load_csv(SCORE_CSV, SCORE_HDR)
    live = score_df[score_df["match_id"]==m]
    
    st.markdown("### Current Scores")
    if not live.empty:
        r = live.groupby(["set_no","team_id"])["points"].sum().unstack(fill_value=0)
        for s in r.index:
            t1_pts = r.loc[s,match["team1_id"]]
            t2_pts = r.loc[s,match["team2_id"]]
            st.write(f"Set {s}: **{team1} {t1_pts} - {t2_pts} {team2}**")
    else:
        st.info("0 - 0")

    # --- Button-Based Scoring Flow ---
    st.divider()
    if "tt_step" not in st.session_state:
        st.session_state["tt_step"] = "SELECT_POINT"
    if "tt_winner" not in st.session_state:
        st.session_state["tt_winner"] = None

    def reset_tt_flow():
        st.session_state["tt_step"] = "SELECT_POINT"
        st.session_state["tt_winner"] = None

    def safe_rerun():
        try:
            st.rerun()
        except AttributeError:
            st.experimental_rerun()

    if st.button("❌ Reset Input"):
        reset_tt_flow()
        safe_rerun()
        
    if st.session_state["tt_step"] == "SELECT_POINT":
        st.markdown(f"#### Who won the point?")
        c1, c2 = st.columns(2)
        if c1.button(f"🏓 {team1}", use_container_width=True):
             st.session_state["tt_winner"] = team1
             st.session_state["tt_step"] = "CONFIRM"
             safe_rerun()
        if c2.button(f"🏓 {team2}", use_container_width=True):
             st.session_state["tt_winner"] = team2
             st.session_state["tt_step"] = "CONFIRM"
             safe_rerun()

    if st.session_state["tt_step"] == "CONFIRM":
        winner = st.session_state["tt_winner"]
        st.info(f"Adding Point for: **{winner}**")
        
        with st.form("tt_point_form"):
             # Set Logic
             set_no = st.selectbox("Set Number", range(1, max_sets+1))
             
             if st.form_submit_button("✅ Confirm Point"):
                 tid = match["team1_id"] if winner == team1 else match["team2_id"]
                 score_df.loc[len(score_df)] = [m, set_no, tid, 1, datetime.now()]
                 save_csv(score_df, SCORE_CSV)
                 st.success(f"Point added for {winner}!")
                 reset_tt_flow()
                 safe_rerun()

    # Show live score
    st.markdown("### Current Scores")
    live = score_df[score_df["match_id"]==m]
    if not live.empty:
        r = live.groupby(["set_no","team_id"])["points"].sum().unstack(fill_value=0)

        for s in r.index:
            t1_pts = r.loc[s,match["team1_id"]] if match["team1_id"] in r.columns else 0
            t2_pts = r.loc[s,match["team2_id"]] if match["team2_id"] in r.columns else 0
            st.markdown(f"**Set {s}:** {team1} **{t1_pts}** - **{t2_pts}** {team2}")
            
    # --- Commentary ---
    st.markdown("---")
    st.subheader("🎙 Commentary (Recent Points)")
    if not live.empty:
        comm_df = live.sort_index(ascending=False).head(10)
        
        for _, row in comm_df.iterrows():
            # Format: Set X | Team scored
            set_n = row['set_no']
            tid = row['team_id']
            # Get winner name
            w_name = team1 if tid == match["team1_id"] else team2
            
            st.markdown(f"**Set {set_n}** | Point for **{w_name}** 🏓")
            st.divider()
    else:
        st.info("No points yet.")

def summary():
    st.subheader("📊 Match Summary")
    df = load_csv(SCORE_CSV, SCORE_HDR)
    if df.empty: return st.info("No scores")

    m = st.selectbox("Match",df["match_id"].unique())
    show = df[df["match_id"]==m]

    if show.empty: return st.info("No score yet")

    match = load_csv(MATCH_CSV, MATCH_HDR)
    meta = match[match["match_id"]==m].iloc[0]
    teams = load_csv(TEAM_CSV, TEAM_HDR)

    t1 = teams.loc[teams["team_id"]==meta["team1_id"],"team_name"].values[0]
    t2 = teams.loc[teams["team_id"]==meta["team2_id"],"team_name"].values[0]

    final = show.groupby(["set_no","team_id"])["points"].sum().unstack(fill_value=0)

    wins_t1 = wins_t2 = 0

    st.write("### Final Scorecard")
    for s in final.index:
        t1_pts = final.loc[s,meta["team1_id"]]
        t2_pts = final.loc[s,meta["team2_id"]]
        result = f"{t1_pts} - {t2_pts}"
        if t1_pts > t2_pts: wins_t1 += 1
        elif t2_pts > t1_pts: wins_t2 += 1
        st.write(f"Set {s}: **{team1} {result} {team2}**")

    st.success(f"🏆 Winner: {team1 if wins_t1>wins_t2 else team2}")

def view_tournaments():
    st.subheader("📋 View Tournaments")

    tournaments = load_csv(T_CSV, T_HDR)
    matches = load_csv(MATCH_CSV, MATCH_HDR)
    teams = load_csv(TEAM_CSV, TEAM_HDR)

    if tournaments.empty:
        st.warning("No tournaments found.")
        return
    
    tournament_list = tournaments["tournament_name"].tolist()
    selected = st.selectbox("Select Tournament", tournament_list)

    if selected:
        st.markdown(f"### Matches in {selected}")

        tid = int(tournaments.loc[
            tournaments["tournament_name"] == selected,
            "tournament_id"
        ].values[0])

        t_matches = matches[matches["tournament_id"] == tid]

        if t_matches.empty:
            st.info("No matches scheduled for this tournament yet.")
        else:
            def get_team(team_id):
                name = teams.loc[teams["team_id"] == team_id, "team_name"]
                return name.values[0] if not name.empty else "Unknown"
            
            display_df = t_matches.copy()
            display_df["Team 1"] = display_df["team1_id"].apply(get_team)
            display_df["Team 2"] = display_df["team2_id"].apply(get_team)
            display_df["Date"] = display_df["match_date"]
            display_df["Format"] = display_df["format"]
            
            st.dataframe(
                display_df[["match_id","Team 1","Team 2","Date","venue","Format"]].reset_index(drop=True)
            )

def run():
    st.title("🏓 Table Tennis Dashboard")

def run_table_tennis():
    st.sidebar.title("Table Tennis Module")
    nav = st.sidebar.radio("Menu",
                           ["Add Tournament","Add Team","Add Player","View Tournaments",
                            "Schedule Match","Update Live Score","Match Summary"])

    if nav=="Add Tournament": add_tournament()
    if nav=="Add Team": add_team()
    if nav=="Add Player": add_player()
    if nav=="View Tournaments": view_tournaments()
    if nav=="Schedule Match": schedule_match()
    if nav=="Update Live Score": update_live()
    if nav=="Match Summary": summary()

