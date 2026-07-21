import streamlit as st
from itertools import combinations
from collections import Counter

RANKS = "23456789TJQKA"
SUITS = "cdhs"
RANK_VALUES = {r: i for i, r in enumerate(RANKS, start=2)}

def parse_card(card_str):
    """Parses card inputs like 'Ah', '10h', or 'ts' reliably."""
    card_str = card_str.strip()
    if not card_str:
        return None
    
    # Standardize '10' inputs to 'T'
    if card_str.startswith("10"):
        card_str = "T" + card_str[2:]
        
    if len(card_str) != 2:
        return None
        
    rank, suit = card_str[0].upper(), card_str[1].lower()
    if rank in RANKS and suit in SUITS:
        return (RANK_VALUES[rank], suit, rank)
    return None

def is_straight(ranks_5):
    """Helper to evaluate 5-card straights including Ace-low wheels."""
    r_set = sorted(list(set(ranks_5)), reverse=True)
    if len(r_set) != 5:
        return False
    if r_set[0] - r_set[4] == 4:
        return True
    if r_set == [14, 5, 4, 3, 2]:  # A-5-4-3-2 Wheel
        return True
    return False

def analyze_plo_hand(hole_str_list, board_str_list):
    # Parse cards safely
    hole_cards = [parse_card(c) for c in hole_str_list]
    board_cards = [parse_card(c) for c in board_str_list]

    # Validate that no inputs failed parsing
    if None in hole_cards or None in board_cards:
        return None

    # Ensure all 7 cards are completely unique
    all_cards = hole_cards + board_cards
    if len(set(all_cards)) != 7:
        return None

    # 1. FLUSH & BACKDOOR FLUSH DRAWS
    board_suits = [c[1] for c in board_cards]
    board_suit_counts = Counter(board_suits)
    
    flush_draw = "None"
    backdoor_flush_draw = "None"

    for suit, count in board_suit_counts.items():
        user_suit_cards = sorted([c[0] for c in hole_cards if c[1] == suit], reverse=True)
        if count == 2 and len(user_suit_cards) >= 2:
            top_rank = user_suit_cards[0]
            if top_rank == 14:
                flush_draw = "Nut Flush Draw"
            elif top_rank == 13:
                flush_draw = "2nd Nut Flush Draw"
            else:
                flush_draw = f"{top_rank}-High Flush Draw"

        elif count == 1 and len(user_suit_cards) >= 2:
            top_rank = user_suit_cards[0]
            if top_rank == 14:
                backdoor_flush_draw = "Nut Backdoor Flush Draw"
            else:
                backdoor_flush_draw = f"{top_rank}-High Backdoor Flush Draw"

    # 2. BLOCKERS
    nut_flush_blockers = 0
    for suit, count in board_suit_counts.items():
        if count in [2, 3]:
            nut_flush_blockers += sum(1 for c in hole_cards if c[0] == 14 and c[1] == suit)

    nut_flush_blocker_str = f"Yes ({nut_flush_blockers})" if nut_flush_blockers > 0 else "No"

    board_ranks = sorted([c[0] for c in board_cards])
    nut_straight_blockers = 0
    needed_nut_rank = None
    
    if board_ranks in [[10, 11, 12], [11, 12, 13]] or max(board_ranks) - min(board_ranks) <= 4:
        needed_nut_rank = 14

    if needed_nut_rank:
        nut_straight_blockers = sum(1 for c in hole_cards if c[0] == needed_nut_rank)

    nut_straight_blocker_str = f"Yes ({nut_straight_blockers})" if nut_straight_blockers > 0 else "No"

    # 3. MADE HAND (Evaluates 6 PLO combinations)
    best_made_hand = "High Card"
    hole_combos = list(combinations(hole_cards, 2))
    
    for combo in hole_combos:
        five_cards = list(combo) + board_cards
        ranks = sorted([c[0] for c in five_cards], reverse=True)
        suits = [c[1] for c in five_cards]
        r_counts = Counter(ranks)

        has_flush = len(set(suits)) == 1
        has_straight = is_straight(ranks)

        if has_flush and has_straight:
            best_made_hand = "Straight Flush"
        elif 3 in r_counts.values() and 2 in r_counts.values():
            best_made_hand = "Full House (Boat)"
        elif has_flush and best_made_hand not in ["Straight Flush"]:
            best_made_hand = "Flush"
        elif has_straight and best_made_hand not in ["Straight Flush", "Full House (Boat)", "Flush"]:
            best_made_hand = "Straight"
        elif 3 in r_counts.values() and best_made_hand in ["High Card", "Pair", "Two Pair"]:
            best_made_hand = "Three of a Kind (Set/Trips)"
        elif list(r_counts.values()).count(2) == 2 and best_made_hand in ["High Card", "Pair"]:
            best_made_hand = "Two Pair"
        elif 2 in r_counts.values() and best_made_hand == "High Card":
            pair_rank = [r for r, count in r_counts.items() if count == 2][0]
            board_ranks_only = [c[0] for c in board_cards]
            if pair_rank == max(board_ranks_only):
                best_made_hand = "Top Pair"
            elif pair_rank == min(board_ranks_only):
                best_made_hand = "Bottom Pair"
            else:
                best_made_hand = "Middle Pair"

    # 4. STRAIGHT DRAW
    straight_draw_str = "Dynamic evaluation pending"

    return {
        "Made Hand": best_made_hand,
        "Flush Draw": flush_draw,
        "Straight Draw": straight_draw_str,
        "Nut Flush Blocker": nut_flush_blocker_str,
        "Nut Straight Blocker": nut_straight_blocker_str,
        "Backdoor Flush Draw": backdoor_flush_draw,
    }

# Streamlit Layout
st.set_page_config(page_title="PLO Flop Evaluator", page_icon="♠", layout="centered")

st.title("♠ PLO Flop Evaluator")
st.write("Enter **4 hole cards** and **3 board cards** (e.g., `Ah`, `Kd`, `10s`, `9c`).")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Hole Cards (4)")
    h1 = st.text_input("Card 1", "Ah", key="h1")
    h2 = st.text_input("Card 2", "Ad", key="h2")
    h3 = st.text_input("Card 3", "Qd", key="h3")
    h4 = st.text_input("Card 4", "Js", key="h4")

with col2:
    st.subheader("Board / Flop (3)")
    b1 = st.text_input("Flop 1", "Jh", key="b1")
    b2 = st.text_input("Flop 2", "Th", key="b2")
    b3 = st.text_input("Flop 3", "2c", key="b3")

st.divider()

if st.button("Evaluate Hand", type="primary", use_container_width=True):
    hole_input = [h1, h2, h3, h4]
    board_input = [b1, b2, b3]
    
    results = analyze_plo_hand(hole_input, board_input)
    
    if results is None:
        st.error("Please enter 7 valid, unique cards (e.g., Ah, Ts, 2c). Check for duplicates or invalid card format.")
    else:
        st.subheader("Hand Analysis Results")
        for key, value in results.items():
            st.markdown(f"**{key}:** `{value}`")
          
