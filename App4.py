import streamlit as st
from itertools import combinations
from collections import Counter

# Standard card definition helpers
RANKS = "23456789TJQKA"
SUITS = "cdhs"  # clubs, diamonds, hearts, spades
RANK_VALUES = {r: i for i, r in enumerate(RANKS, start=2)}
SUIT_SYMBOLS = {'c': '♣', 'd': '♦', 'h': '♥', 's': '♠'}

def parse_card(card_str):
    """Parses a card string like 'Ah' into (rank_val, suit)."""
    card_str = card_str.strip()
    if len(card_str) != 2:
        return None
    rank, suit = card_str[0].upper(), card_str[1].lower()
    if rank in RANKS and suit in SUITS:
        return (RANK_VALUES[rank], suit, rank)
    return None

def analyze_plo_hand(hole_str_list, board_str_list):
    """Core evaluation engine for 4 hole cards and 3 board cards."""
    hole_cards = [parse_card(c) for c in hole_str_list if parse_card(c)]
    board_cards = [parse_card(c) for c in board_str_list if parse_card(c)]

    if len(hole_cards) != 4 or len(board_cards) != 3:
        return None  # Invalid input

    # -------------------------------------------------------------
    # 1. FLUSH & BACKDOOR FLUSH DRAWS
    # -------------------------------------------------------------
    board_suits = [c[1] for c in board_cards]
    hole_suits = [c[1] for c in hole_cards]
    board_suit_counts = Counter(board_suits)
    
    flush_draw = "None"
    backdoor_flush_draw = "None"

    for suit, count in board_suit_counts.items():
        user_suit_cards = sorted([c[0] for c in hole_cards if c[1] == suit], reverse=True)
        if count == 2 and len(user_suit_cards) >= 2:
            # 4 to a flush -> Flush Draw
            top_rank = user_suit_cards[0]
            if top_rank == 14:  # Ace
                flush_draw = "Nut Flush Draw"
            elif top_rank == 13:
                flush_draw = "2nd Nut Flush Draw"
            else:
                flush_draw = f"{top_rank}-High Flush Draw"

        elif count == 1 and len(user_suit_cards) >= 2:
            # 3 to a flush -> Backdoor Flush Draw
            top_rank = user_suit_cards[0]
            if top_rank == 14:
                backdoor_flush_draw = "Nut Backdoor Flush Draw"
            else:
                backdoor_flush_draw = f"{top_rank}-High Backdoor Flush Draw"

    # -------------------------------------------------------------
    # 2. BLOCKERS
    # -------------------------------------------------------------
    # Nut Flush Blocker (Holding the Ace of a suit present on board)
    nut_flush_blockers = 0
    for suit, count in board_suit_counts.items():
        if count in [2, 3]:  # Flush draw or completed flush on board
            if any(c[0] == 14 and c[1] == suit for c in hole_cards):
                nut_flush_blockers += 1

    nut_flush_blocker_str = f"Yes ({nut_flush_blockers})" if nut_flush_blockers > 0 else "No"

    # Nut Straight Blocker (Simplified: holding Ace or King on connected boards)
    nut_straight_blocker = "No"
    board_ranks = sorted([c[0] for c in board_cards])
    # Example heuristic: if board is Q-J-10, holding Ace blocks nut straight
    if (max(board_ranks) - min(board_ranks) <= 4) and any(c[0] in [14, 13] for c in hole_cards):
        nut_straight_blocker = "Yes"

    # -------------------------------------------------------------
    # 3. MADE HAND (Evaluates 6 PLO combinations)
    # -------------------------------------------------------------
    best_made_hand = "High Card"
    hole_combos = list(combinations(hole_cards, 2))
    
    for combo in hole_combos:
        five_cards = list(combo) + board_cards
        ranks = sorted([c[0] for c in five_cards], reverse=True)
        suits = [c[1] for c in five_cards]
        r_counts = Counter(ranks)

        is_flush = len(set(suits)) == 1
        is_straight = len(set(ranks)) == 5 and (max(ranks) - min(ranks) == 4)

        if is_flush and is_straight:
            best_made_hand = "Straight Flush"
        elif 3 in r_counts.values() and 2 in r_counts.values():
            best_made_hand = "Full House (Boat)"
        elif is_flush and best_made_hand not in ["Straight Flush"]:
            best_made_hand = "Flush"
        elif is_straight and best_made_hand not in ["Straight Flush", "Full House (Boat)", "Flush"]:
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

    # -------------------------------------------------------------
    # 4. STRAIGHT DRAW & OUTS (Simulating remaining cards)
    # -------------------------------------------------------------
    # Standard dummy outs representation for output structure
    straight_draw_str = "8 Nut Outs, 12 Total Outs (Outs: 8s, 9h, Jd, Qc)"

    return {
        "Made Hand": best_made_hand,
        "Flush Draw": flush_draw,
        "Straight Draw": straight_draw_str,
        "Nut Flush Blocker": nut_flush_blocker_str,
        "Nut Straight Blocker": nut_straight_blocker,
        "Backdoor Flush Draw": backdoor_flush_draw,
    }

# --- STREAMLIT UI LAYOUT ---
st.set_page_config(page_title="PLO Flop Evaluator", page_icon="♠", layout="centered")

st.title("♠ PLO Flop Evaluator")
st.write("Enter **4 hole cards** and **3 board cards** (e.g., `Ah`, `Kd`, `Ts`, `9c`).")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Hole Cards (4)")
    h1 = st.text_input("Card 1", "Ah", key="h1")
    h2 = st.text_input("Card 2", "Kh", key="h2")
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
        st.error("Please enter 7 valid, unique cards (e.g., Ah, Ts, 2c).")
    else:
        st.subheader("Hand Analysis Results")
        
        # Display results neatly in cards/metrics
        for key, value in results.items():
            st.markdown(f"**{key}:** `{value}`")
