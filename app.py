from itertools import combinations
import streamlit as st

# ==========================================
# 1. CORE PLO LOGIC & CALCULATIONS
# ==========================================

RANK_MAP = {r: i for i, r in enumerate("23456789TJQKA", start=2)}
INV_RANK = {i: r for r, i in RANK_MAP.items()}


def parse_ranks(cards_str):
    """Parses ranks from strings like 'Jh Ts 8c 5s' or 'J T 8 5'."""
    return [RANK_MAP[c[0].upper()] for c in cards_str.split()]


def is_straight(five_ranks):
    """Checks if any 5 ranks contain a valid straight."""
    ranks = sorted(set(five_ranks))
    if len(ranks) < 5:
        return False

    # Check 5-card sequence
    for i in range(len(ranks) - 4):
        if ranks[i + 4] - ranks[i] == 4:
            return True

    # Check Ace-low straight (A-2-3-4-5)
    if set([14, 2, 3, 4, 5]).issubset(set(ranks)):
        return True

    return False


def get_highest_straight_rank(five_ranks):
    """Returns the highest rank of a completed straight (for Nut checks)."""
    ranks = sorted(set(five_ranks))
    highest = 0
    for i in range(len(ranks) - 4):
        if ranks[i + 4] - ranks[i] == 4:
            highest = max(highest, ranks[i + 4])
    if set([14, 2, 3, 4, 5]).issubset(set(ranks)):
        highest = max(highest, 5)
    return highest


def analyze_plo_straight_draw(hand_str, board_str):
    """Calculates total outs, nut outs, and classifies the draw type."""
    hand = parse_ranks(hand_str)
    board = parse_ranks(board_str)

    seen_cards = hand + board
    outs = {}

    # Check every potential turn/river card rank (2 to Ace)
    for candidate_rank in range(2, 15):
        cards_left = 4 - seen_cards.count(candidate_rank)
        if cards_left <= 0:
            continue

        full_board = board + [candidate_rank]
        makes_straight = False
        my_best_straight = 0

        # PLO Mandatory Rule: Exactly 2 from hand, 3 from board
        for h_combo in combinations(hand, 2):
            for b_combo in combinations(full_board, 3):
                test_5 = list(h_combo) + list(b_combo)
                if is_straight(test_5):
                    makes_straight = True
                    my_best_straight = max(
                        my_best_straight,
                        get_highest_straight_rank(test_5)
                    )

        if makes_straight:
            # Check if it's the NUT straight on this board
            global_max_straight = 0
            all_possible_hole = combinations(range(2, 15), 2)
            for opp_h in all_possible_hole:
                for b_combo in combinations(full_board, 3):
                    test_opp = list(opp_h) + list(b_combo)
                    if is_straight(test_opp):
                        global_max_straight = max(
                            global_max_straight,
                            get_highest_straight_rank(test_opp)
                        )

            is_nut = (my_best_straight == global_max_straight)
            outs[INV_RANK[candidate_rank]] = {
                'count': cards_left,
                'is_nut': is_nut
            }

    total_outs = sum(v['count'] for v in outs.values())
    nut_outs = sum(v['count'] for v in outs.values() if v['is_nut'])

    # Categorize draw type
    if total_outs >= 20:
        draw_type = "20-Out Mega Wrap"
    elif total_outs >= 16:
        draw_type = "16-Out Wrap"
    elif total_outs >= 13:
        draw_type = "13-Out Wrap"
    elif total_outs >= 9:
        draw_type = "9-Out Wrap"
    elif total_outs == 8:
        draw_type = "Open-Ended Straight Draw"
    elif total_outs == 4:
        draw_type = "Gutshot"
    else:
        draw_type = "Weak/No Straight Draw"

    return {
        'draw_type': draw_type,
        'total_outs': total_outs,
        'nut_outs': nut_outs,
        'out_details': outs
    }


# ==========================================
# 2. STREAMLIT MOBILE INTERFACE
# ==========================================

st.set_page_config(page_title="PLO Wrap Calculator", layout="centered")

st.title("♠️ PLO Wrap Calculator")
st.write("Select your hand and board to calculate straight outs and nut draws.")

card_options = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]

# --- Board Input ---
st.subheader("Board Cards (Flop)")
c1, c2, c3 = st.columns(3)
b1 = c1.selectbox("Board 1", card_options, index=7)  # Default: 9
b2 = c2.selectbox("Board 2", card_options, index=5)  # Default: 7
b3 = c3.selectbox("Board 3", card_options, index=0)  # Default: 2

# --- Hole Cards Input ---
st.subheader("Your Hole Cards")
h1_col, h2_col, h3_col, h4_col = st.columns(4)
h1 = h1_col.selectbox("Card 1", card_options, index=9)   # Default: J
h2 = h2_col.selectbox("Card 2", card_options, index=8)   # Default: T
h3 = h3_col.selectbox("Card 3", card_options, index=6)   # Default: 8
h4 = h4_col.selectbox("Card 4", card_options, index=3)   # Default: 5

st.markdown("---")

# --- Analysis & Output ---
if st.button("Analyze Hand", use_container_width=True):
    # Pass dummy suits (s, d, c, h) since straight logic only depends on rank
    board_str = f"{b1}s {b2}d {b3}c"
    hand_str = f"{h1}d {h2}s {h3}c {h4}s"

    result = analyze_plo_straight_draw(hand_str, board_str)

    st.subheader("Results")
    st.info(f"**Draw Type:** {result['draw_type']}")

    m1, m2 = st.columns(2)
    m1.metric("Total Outs", result['total_outs'])
    m2.metric("Nut Outs", result['nut_outs'])

    st.write("**Hitting Cards Breakdown:**")
    if result['out_details']:
        for card, info in result['out_details'].items():
            nut_status = "🟢 Nut Out" if info['is_nut'] else "⚠️ Non-Nut Out"
            st.write(f"- **{card}**: {info['count']} outs ({nut_status})")
    else:
        st.write("No straight outs found.")
      
