import random
from itertools import combinations
import streamlit as st

# ==========================================
# 1. CORE PLO LOGIC & CALCULATIONS
# ==========================================

RANK_MAP = {r: i for i, r in enumerate("23456789TJQKA", start=2)}
INV_RANK = {i: r for r, i in RANK_MAP.items()}
ALL_RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]

DRAW_CATEGORIES = [
    "20-Out Mega Wrap",
    "16-Out Wrap",
    "13-Out Wrap",
    "9-Out Wrap",
    "Open-Ended Straight Draw",
    "Gutshot",
    "No Straight Draw"
]


def parse_ranks(cards_str):
    return [RANK_MAP[c[0].upper()] for c in cards_str.split()]


def is_straight(five_ranks):
    ranks = sorted(set(five_ranks))
    if len(ranks) < 5:
        return False
    for i in range(len(ranks) - 4):
        if ranks[i + 4] - ranks[i] == 4:
            return True
    if set([14, 2, 3, 4, 5]).issubset(set(ranks)):
        return True
    return False


def get_highest_straight_rank(five_ranks):
    ranks = sorted(set(five_ranks))
    highest = 0
    for i in range(len(ranks) - 4):
        if ranks[i + 4] - ranks[i] == 4:
            highest = max(highest, ranks[i + 4])
    if set([14, 2, 3, 4, 5]).issubset(set(ranks)):
        highest = max(highest, 5)
    return highest


def analyze_plo_straight_draw(hand_str, board_str):
    hand = parse_ranks(hand_str)
    board = parse_ranks(board_str)
    seen_cards = hand + board
    outs = {}

    for candidate_rank in range(2, 15):
        cards_left = 4 - seen_cards.count(candidate_rank)
        if cards_left <= 0:
            continue

        full_board = board + [candidate_rank]
        makes_straight = False
        my_best_straight = 0

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
        draw_type = "No Straight Draw"

    return {
        'draw_type': draw_type,
        'total_outs': total_outs,
        'nut_outs': nut_outs,
        'out_details': outs
    }


# ==========================================
# 2. DRILL GENERATOR & STATE HELPERS
# ==========================================

def generate_new_question():
    """Generates a random hand, flop, correct answer, and 4 choices."""
    suits = ['s', 'h', 'd', 'c']
    deck = [f"{r}{s}" for r in ALL_RANKS for s in suits]
    dealt = random.sample(deck, 7)

    hand = dealt[:4]
    board = dealt[4:]

    hand_str = " ".join(hand)
    board_str = " ".join(board)

    analysis = analyze_plo_straight_draw(hand_str, board_str)
    correct_answer = analysis['draw_type']

    # Generate choices: Always include 'No Straight Draw' and correct answer
    choices = {"No Straight Draw", correct_answer}
    pool = [c for c in DRAW_CATEGORIES if c not in choices]
    
    # Fill up to 4 total choices
    while len(choices) < 4:
        choices.add(random.choice(pool))

    choice_list = list(choices)
    random.shuffle(choice_list)

    st.session_state.hand = hand
    st.session_state.board = board
    st.session_state.analysis = analysis
    st.session_state.correct_answer = correct_answer
    st.session_state.choices = choice_list
    st.session_state.answered = False
    st.session_state.user_choice = None


# ==========================================
# 3. STREAMLIT INTERFACE
# ==========================================

st.set_page_config(page_title="PLO Straight Draw Trainer", layout="centered")
st.title("🎯 PLO Straight Draw Trainer")

# Initialize session states
if "score" not in st.session_state:
    st.session_state.score = 0
if "total" not in st.session_state:
    st.session_state.total = 0
if "hand" not in st.session_state:
    generate_new_question()

# Scoreboard
col_s1, col_s2 = st.columns(2)
col_s1.metric("Score", f"{st.session_state.score} / {st.session_state.total}")
if st.session_state.total > 0:
    pct = int((st.session_state.score / st.session_state.total) * 100)
    col_s2.metric("Accuracy", f"{pct}%")

st.markdown("---")

# Display current problem
st.subheader("Flop Cards")
st.title("  ".join(st.session_state.board))

st.subheader("Your Hand")
st.title("  ".join(st.session_state.hand))

st.markdown("---")

# Quiz Options Form
if not st.session_state.answered:
    st.write("### What type of straight draw do you have?")
    user_selection = st.radio(
        "Select your answer:",
        st.session_state.choices,
        key="radio_choice"
    )

    if st.button("Submit Answer", use_container_width=True):
        st.session_state.answered = True
        st.session_state.user_choice = user_selection
        st.session_state.total += 1

        if user_selection == st.session_state.correct_answer:
            st.session_state.score += 1
        st.rerun()

# Feedback and Explanation Section
else:
    if st.session_state.user_choice == st.session_state.correct_answer:
        st.success(f"🎉 **Correct!** It is a **{st.session_state.correct_answer}**.")
    else:
        st.error(
            f"❌ **Incorrect.** You selected *{st.session_state.user_choice}*.\n\n"
            f"The correct answer is **{st.session_state.correct_answer}**."
        )

    # Hand Breakdown Details
    res = st.session_state.analysis
    with st.expander("Show Detailed Hand Analysis", expanded=True):
        st.write(f"- **Total Outs:** {res['total_outs']}")
        st.write(f"- **Nut Outs:** {res['nut_outs']}")
        st.write("**Hitting Cards:**")
        if res['out_details']:
            for card, info in res['out_details'].items():
                status = "🟢 Nut Out" if info['is_nut'] else "⚠️ Non-Nut Out"
                st.write(f"  * **{card}**: {info['count']} outs ({status})")
        else:
            st.write("  * None")

    if st.button("Next Hand ➡️", use_container_width=True):
        generate_new_question()
        st.rerun()
      
