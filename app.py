import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="RoyaleOracle - Balance Predictor", layout="wide", page_icon="👑")

# --- 1. SEED DATA (Curated Meta Snapshot + Balance History) ---
@st.cache_data
def load_card_data():
    data = [
        {"name": "Evo Bomber", "role": "troop", "wr": 57.8, "ur": 24.5, "days_since_change": 45, "tweak_count_2yr": 2},
        {"name": "Cannoneer", "role": "troop", "wr": 55.4, "ur": 21.0, "days_since_change": 70, "tweak_count_2yr": 1},
        {"name": "Poison", "role": "spell", "wr": 54.8, "ur": 28.0, "days_since_change": 120, "tweak_count_2yr": 1},
        {"name": "Little Prince", "role": "troop", "wr": 54.2, "ur": 18.5, "days_since_change": 30, "tweak_count_2yr": 3},
        {"name": "Knight", "role": "troop", "wr": 51.5, "ur": 14.2, "days_since_change": 90, "tweak_count_2yr": 2},
        {"name": "The Log", "role": "spell", "wr": 50.2, "ur": 39.5, "days_since_change": 240, "tweak_count_2yr": 1},
        {"name": "Hog Rider", "role": "win_con", "wr": 49.6, "ur": 11.2, "days_since_change": 400, "tweak_count_2yr": 0},
        {"name": "Fireball", "role": "spell", "wr": 50.1, "ur": 26.0, "days_since_change": 180, "tweak_count_2yr": 0},
        {"name": "Musketeer", "role": "troop", "wr": 48.9, "ur": 8.1, "days_since_change": 150, "tweak_count_2yr": 1},
        {"name": "Wizard", "role": "troop", "wr": 49.8, "ur": 2.1, "days_since_change": 80, "tweak_count_2yr": 5},
        {"name": "Elixir Golem", "role": "win_con", "wr": 51.2, "ur": 2.5, "days_since_change": 65, "tweak_count_2yr": 4},
        {"name": "Rascals", "role": "troop", "wr": 42.1, "ur": 1.4, "days_since_change": 190, "tweak_count_2yr": 1},
        {"name": "Barbarian Hut", "role": "building", "wr": 38.5, "ur": 0.4, "days_since_change": 300, "tweak_count_2yr": 3},
        {"name": "Night Witch", "role": "troop", "wr": 43.8, "ur": 1.8, "days_since_change": 140, "tweak_count_2yr": 2},
        {"name": "Goblin Gang", "role": "troop", "wr": 49.2, "ur": 9.4, "days_since_change": 110, "tweak_count_2yr": 1},
        {"name": "Electro Dragon", "role": "troop", "wr": 44.5, "ur": 1.9, "days_since_change": 210, "tweak_count_2yr": 0},
        {"name": "Giant", "role": "win_con", "wr": 53.6, "ur": 14.1, "days_since_change": 60, "tweak_count_2yr": 2},
    ]
    return pd.DataFrame(data)

# --- 2. PREDICTION LOGIC ENGINE ---
def compute_predictions(df):
    results = []
    for _, row in df.iterrows():
        wr = row['wr']
        ur = row['ur']
        days = row['days_since_change']
        tweaks = row['tweak_count_2yr']
        role = row['role']

        ur_base = 22.0 if role == 'spell' else 8.0
        ur_excess = max(0, ur - ur_base)
        ur_deficit = max(0, (ur_base * 0.4) - ur)
        
        # Cooldown penalty for recently changed cards (<60 days)
        cooldown = min(1.0, days / 60.0)

        # Nerf Risk
        wr_nerf = max(0, wr - 53.0)
        nerf_score = min(96.0, ((wr_nerf * 9.0) + (ur_excess * 2.5)) * cooldown) if wr > 52.0 else 4.0

        # Buff Priority
        wr_buff = max(0, 47.0 - wr)
        buff_score = min(96.0, ((wr_buff * 8.0) + (ur_deficit * 3.5)) * cooldown) if wr < 48.5 else 4.0

        # Rework Probability (Oscillating cards / unfixable designs)
        rework_score = 75.0 if (tweaks >= 4 and ur < 3.5) else 10.0

        # Assign outcome label
        top_score = max(nerf_score, buff_score, rework_score)
        if top_score < 40.0:
            decision = "Balanced / Safe"
        elif top_score == nerf_score:
            decision = "Nerf"
        elif top_score == buff_score:
            decision = "Buff"
        else:
            decision = "Rework"

        results.append({
            "Nerf_Risk": round(nerf_score, 1),
            "Buff_Priority": round(buff_score, 1),
            "Rework_Index": round(rework_score, 1),
            "Forecast": decision
        })
    return pd.concat([df, pd.DataFrame(results)], axis=1)

# --- 3. UI LAYOUT ---
st.title("👑 RoyaleOracle: Next Balance Patch Predictor")
st.caption("AI & Telemetry-based balancing engine for Clash Royale esports competitive meta.")

df = compute_predictions(load_card_data())

# Top KPI highlights
top_nerf = df.sort_values(by="Nerf_Risk", ascending=False).iloc[0]
top_buff = df.sort_values(by="Buff_Priority", ascending=False).iloc[0]
top_rework = df.sort_values(by="Rework_Index", ascending=False).iloc[0]

c1, c2, c3 = st.columns(3)
c1.metric(label="🔥 #1 Nerf Target", value=top_nerf['name'], delta=f"{top_nerf['Nerf_Risk']}% Risk", delta_color="inverse")
c2.metric(label="🛠️ #1 Buff Priority", value=top_buff['name'], delta=f"{top_buff['Buff_Priority']}% Priority")
c3.metric(label="🔄 #1 Rework Candidate", value=top_rework['name'], delta=f"{top_rework['Rework_Index']}% Index", delta_color="off")

st.divider()

# --- 4. QUADRANT SCATTER PLOT ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("🎯 Meta Quadrant Chart")
    
    fig = px.scatter(
        df, x="ur", y="wr", text="name", color="Forecast",
        color_discrete_map={"Nerf": "#EF4444", "Buff": "#3B82F6", "Rework": "#F59E0B", "Balanced / Safe": "#10B981"},
        labels={"ur": "Grand Challenge Use Rate (%)", "wr": "Win Rate (%)"},
        hover_data=["days_since_change", "tweak_count_2yr", "Nerf_Risk", "Buff_Priority"]
    )
    
    # Balance zones
    fig.add_hrect(y0=54, y1=62, fillcolor="red", opacity=0.08, line_width=0)
    fig.add_hrect(y0=35, y1=45, fillcolor="blue", opacity=0.08, line_width=0)
    fig.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="Ideal 50% WR")
    
    fig.update_traces(textposition='top center', marker=dict(size=12))
    fig.update_layout(height=480, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

# --- 5. INTERACTIVE "WHAT-IF" SANDBOX ---
with col_right:
    st.subheader("🧪 'What-If' Balance Sandbox")
    st.caption("Simulate meta shifts and see instant predictions.")
    
    selected_card = st.selectbox("Select a Card", df['name'].tolist())
    card_info = df[df['name'] == selected_card].iloc[0]
    
    sim_wr = st.slider("Simulated Win Rate (%)", 35.0, 65.0, float(card_info['wr']), 0.5)
    sim_ur = st.slider("Simulated Use Rate (%)", 0.0, 45.0, float(card_info['ur']), 0.5)
    
    # Run sandbox prediction
    temp_df = pd.DataFrame([{
        "name": selected_card, "role": card_info['role'], "wr": sim_wr, "ur": sim_ur,
        "days_since_change": card_info['days_since_change'], "tweak_count_2yr": card_info['tweak_count_2yr']
    }])
    sim_res = compute_predictions(temp_df).iloc[0]
    
    st.markdown(f"**Predicted Patch Action:**")
    color = "red" if sim_res['Forecast'] == "Nerf" else "blue" if sim_res['Forecast'] == "Buff" else "green"
    st.markdown(f"### :{color}[{sim_res['Forecast']}]")
    
    st.write(f"- **Nerf Risk:** `{sim_res['Nerf_Risk']}%`")
    st.write(f"- **Buff Priority:** `{sim_res['Buff_Priority']}%`")
    st.write(f"- **Rework Urgency:** `{sim_res['Rework_Index']}%`")

# --- 6. DATA TABLE ---
st.subheader("📋 Card Intelligence Registry")
st.dataframe(
    df[["name", "role", "wr", "ur", "days_since_change", "Nerf_Risk", "Buff_Priority", "Rework_Index", "Forecast"]],
    use_container_width=True
)