import time
import random
import streamlit as st
import streamlit.components.v1 as components
from itertools import combinations

# ==========================================
# 1. CORE ENGINE & CALCULATIONS
# ==========================================

RANK_MAP = {r: i for i, r in enumerate("23456789TJQKA", start=2)}
INV_RANK = {i: r for r, i in RANK_MAP.items()}
ALL_RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]

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

        # Enforces PLO rules: Exactly 2 hole cards + 3 board cards
        for h_combo in combinations(hand, 2):
            for b_combo in combinations(full_board, 3):
                test_5 = list(h_combo) + list(b_combo)
                if is_straight(test_5):
                    makes_straight = True
                    my_best_straight = max(my_best_straight, get_highest_straight_rank(test_5))

        if makes_straight:
            global_max_straight = 0
            all_possible_hole = combinations(range(2, 15), 2)
            for opp_h in all_possible_hole:
                for b_combo in combinations(full_board, 3):
                    test_opp = list(opp_h) + list(b_combo)
                    if is_straight(test_opp):
                        global_max_straight = max(global_max_straight, get_highest_straight_rank(test_opp))

            is_nut = (my_best_straight == global_max_straight)
            outs[INV_RANK[candidate_rank]] = {
                'count': cards_left,
                'is_nut': is_nut
            }

    total_outs = sum(v['count'] for v in outs.values())
    nut_outs = sum(v['count'] for v in outs.values() if v['is_nut'])

    return {
        'total_outs': total_outs,
        'nut_outs': nut_outs,
        'out_details': outs
    }

# ==========================================
# 2. DRILL GENERATOR & STATE MANAGEMENT
# ==========================================

def generate_new_question(board_type="Random"):
    suits = ['s', 'h', 'd', 'c']
    deck = [f"{r}{s}" for r in ALL_RANKS for s in suits]

    if board_type == "Flop Only":
        num_board_cards = 3
    elif board_type == "Turn Only":
        num_board_cards = 4
    else:
        num_board_cards = random.choice([3, 4])

    dealt = random.sample(deck, 4 + num_board_cards)
    hand = dealt[:4]
    board = dealt[4:]

    analysis = analyze_plo_straight_draw(" ".join(hand), " ".join(board))

    # Construct the target combined answer: "Total Outs (Nut Outs)"
    correct_tuple = f"{analysis['total_outs']} Outs ({analysis['nut_outs']} Nut)"

    # Build plausible distractor choices
    distractors = set()
    distractors.add(correct_tuple)
    
    while len(distractors) < 4:
        # Create realistic miscounts (+/- 4 outs)
        d_tot = max(0, analysis['total_outs'] + random.choice([-4, -3, -1, 1, 3, 4]))
        d_nut = max(0, min(d_tot, analysis['nut_outs'] + random.choice([-4, -2, -1, 0, 1, 2])))
        distractors.add(f"{d_tot} Outs ({d_nut} Nut)")

    choice_list = list(distractors)
    random.shuffle(choice_list)

    st.session_state.hand = hand
    st.session_state.board = board
    st.session_state.street = "Flop" if num_board_cards == 3 else "Turn"
    st.session_state.analysis = analysis
    st.session_state.correct_answer = correct_tuple
    st.session_state.choices = choice_list
    st.session_state.answered = False
    st.session_state.user_choice = None
    st.session_state.start_time = time.time()

def process_answer(selection):
    st.session_state.answered = True
    st.session_state.user_choice = selection
    st.session_state.total += 1
    if selection == st.session_state.correct_answer:
        st.session_state.score += 1

# ==========================================
# 3. STREAMLIT & GAMIFIED UI
# ==========================================

st.set_page_config(page_title="PLO Rapid-Fire Drill", layout="centered")

# Custom CSS for high-contrast visual styling
st.markdown("""
    <style>
    .card-badge {
        display: inline-block;
        background-color: #1e222d;
        color: #ffffff;
        font-weight: bold;
        padding: 8px 14px;
        margin: 3px;
        border-radius: 8px;
        border: 1px solid #363c4e;
        font-size: 24px;
        font-family: monospace;
    }
    .red-suit { color: #ff4b4b; }
    .black-suit { color: #e0e0e0; }
    
    .stButton>button {
        height: 60px;
        font-size: 18px !important;
        font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

def render_cards(cards):
    html = ""
    for c in cards:
        rank, suit = c[0], c[1]
        suit_class = "red-suit" if suit in ['h', 'd'] else "black-suit"
        suit_symbol = {'s':'♠', 'h':'♥', 'd':'♦', 'c':'♣'}[suit]
        html += f"<span class='card-badge'>{rank}<span class='{suit_class}'>{suit_symbol}</span></span>"
    return html

# Sidebar Control
board_mode = st.sidebar.selectbox("Street Mode", ["Random (Flop or Turn)", "Flop Only", "Turn Only"])
mode_map = {"Random (Flop or Turn)": "Random", "Flop Only": "Flop Only", "Turn Only": "Turn Only"}

# Session State Setup
if "score" not in st.session_state:
    st.session_state.score = 0
if "total" not in st.session_state:
    st.session_state.total = 0
if "hand" not in st.session_state:
    generate_new_question(mode_map[board_mode])

# Check for JS-triggered timeout on rerun
if st.session_state.get("timeout_triggered", False) and not st.session_state.answered:
    st.session_state.timeout_triggered = False
    process_answer("TIMEOUT")

# Scoreboard
c1, c2 = st.columns(2)
c1.metric("Score", f"{st.session_state.score} / {st.session_state.total}")
pct = int((st.session_state.score / st.session_state.total) * 100) if st.session_state.total > 0 else 0
c2.metric("Accuracy", f"{pct}%")

st.markdown("---")

# Visual Display of Cards
st.write(f"### Board ({st.session_state.street})")
st.markdown(render_cards(st.session_state.board), unsafe_allow_html=True)

st.write("### Your Hand")
st.markdown(render_cards(st.session_state.hand), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 10-Second JS Countdown Timer Engine
if not st.session_state.answered:
    # Component passes a signal back on timeout
    timeout_event = components.html("""
        <div style="font-family: sans-serif; font-weight: bold; margin-bottom: 5px; color: #ffffff;">
            ⏱️ Time Remaining: <span id="timer" style="color: #ff4b4b;">10</span>s
        </div>
        <div style="width: 100%; background-color: #333; height: 12px; border-radius: 6px;">
            <div id="bar" style="width: 100%; background-color: #ff4b4b; height: 12px; border-radius: 6px; transition: width 1s linear;"></div>
        </div>
        <script>
            var left = 10;
            var interval = setInterval(function() {
                left--;
                if (left <= 0) {
                    clearInterval(interval);
                    // Force a Streamlit state trigger
                    const btn = window.parent.document.querySelector('button[kind="primary"]');
                    window.parent.postMessage({type: 'streamlit:setComponentValue', value: 'TIMEOUT'}, '*');
                }
                document.getElementById('timer').innerHTML = left;
                document.getElementById('bar').style.width = (left * 10) + '%';
            }, 1000);
        </script>
    """, height=50)

    # Secondary Python-side timeout check in case of lag
    if time.time() - st.session_state.start_time >= 10.5:
        process_answer("TIMEOUT")
        st.rerun()

    st.write("**Identify Total Outs & Nut Outs:**")
    
    # 2x2 Grid of Rapid Answer Buttons
    col1, col2 = st.columns(2)
    for i, choice in enumerate(st.session_state.choices):
        target_col = col1 if i % 2 == 0 else col2
        if target_col.button(choice, key=f"btn_{i}", use_container_width=True):
            process_answer(choice)
            st.rerun()

# Feedback Banner State
else:
    is_correct = (st.session_state.user_choice == st.session_state.correct_answer)
    
    if is_correct:
        st.success(f"⚡ **CORRECT!** You selected **{st.session_state.user_choice}**")
    elif st.session_state.user_choice == "TIMEOUT":
        st.error(f"⏰ **WRONG! TIME OUT!** You ran out of time.\n\nCorrect answer: **{st.session_state.correct_answer}**")
    else:
        st.error(f"❌ **WRONG!** You picked *{st.session_state.user_choice}*.\n\nCorrect answer: **{st.session_state.correct_answer}**")

    # Detailed Analysis Breakdown
    res = st.session_state.analysis
    with st.expander("Show Hand Breakdown", expanded=True):
        st.write(f"- **Total Outs:** {res['total_outs']}")
        st.write(f"- **Nut Outs:** {res['nut_outs']}")
        st.write("**Out Details:**")
        if res['out_details']:
            for card, info in res['out_details'].items():
                status = "🟢 Nut Out" if info['is_nut'] else "⚠️ Non-Nut Out"
                st.write(f"  * **{card}**: {info['count']} card(s) ({status})")
        else:
            st.write("  * No straight outs")

    if st.button("Next Hand ➡️", type="primary", use_container_width=True):
        generate_new_question(mode_map[board_mode])
        st.rerun()
      
