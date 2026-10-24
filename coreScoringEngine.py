import numpy as np

def predict_balance(card):
    """
    card dict expects:
    - wr: Win rate (e.g., 56.5)
    - ur: Use rate (e.g., 18.2)
    - role: 'win_con', 'spell', or 'troop'
    - days_since_change: int
    - tweak_count_2yr: int
    """
    wr, ur = card['wr'], card['ur']
    days = card['days_since_change']
    
    # 1. Normalize use rate by role (Spells have higher baseline use rate)
    ur_baseline = 18.0 if card['role'] == 'spell' else 8.0
    ur_excess = max(0, ur - ur_baseline)
    ur_deficit = max(0, (ur_baseline * 0.4) - ur)
    
    # 2. Cooldown Factor: Recently changed cards are rarely touched immediately
    cooldown_mult = min(1.0, days / 60.0)  # full risk after ~2 balance cycles (60 days)
    
    # 3. Nerf Score (Dominant Win Rate + High Usage)
    wr_nerf_excess = max(0, wr - 54.0)
    nerf_raw = (wr_nerf_excess * 8.0) + (ur_excess * 3.0)
    nerf_prob = min(95.0, nerf_raw * cooldown_mult) if wr > 52.0 else 5.0
    
    # 4. Buff Score (Depressed Win Rate + Near-zero Usage)
    wr_buff_deficit = max(0, 47.0 - wr)
    buff_raw = (wr_buff_deficit * 7.0) + (ur_deficit * 4.0)
    buff_prob = min(95.0, buff_raw * cooldown_mult) if wr < 49.0 else 5.0
    
    # 5. Rework Score (Frequent bounces, or extremely skewed playrates)
    rework_prob = 10.0
    if card['tweak_count_2yr'] >= 3 and 48.0 <= wr <= 52.0 and ur < 3.0:
        # Card is balanced on paper but nobody plays it (Dead card identity)
        rework_prob = 75.0
    elif card['tweak_count_2yr'] >= 4:
        # Constant balance headache (e.g., Elixir Golem, Wizard)
        rework_prob = 65.0
        
    return {
        "Nerf": round(nerf_prob, 1),
        "Buff": round(buff_prob, 1),
        "Rework": round(rework_prob, 1),
        "Safe": round(max(0, 100 - (nerf_prob + buff_prob + rework_prob)), 1)
    }