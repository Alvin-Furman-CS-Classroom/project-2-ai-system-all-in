"""
Rule-based hand playability using propositional logic.
Rules combine hand strength, position, stack size, and opponent tendency.
"""

# Ordered list of 169 hands (rank 1 = best), matching POKER_HAND_WIN_PERCENTAGES.md.
# Tier: 1-30 Premium, 31-60 Strong, 61-87 Playable, 88-116 Marginal, 117-169 Weak.
HAND_RANK_LIST = [
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "KAs", "QAs", "JAs", "KAo", "QAo", "TAs", "66", "JAo", "QKs", "9As", "TAo", "JKs", "8As", "TKs", "5As", "QKo", "9Ao", "JKo", "7As", "TKo", "JQs", "6As",
    "8Ao", "4As", "55", "9Ks", "3As", "6Ao", "8Ks", "TQs", "JQo", "2As", "9Ko", "9Qs", "TJs", "7Ks", "5Ao", "4Ao", "7Ao", "6Ks", "44", "TQo", "7Ko", "3Ao", "9Qo", "8Qs", "8Ko", "9Js", "TJo", "5Ks", "2Ao", "6Ko",
    "4Ks", "33", "8Js", "7Qs", "9Jo", "5Ko", "3Ks", "8Qo", "9Ts", "5Qs", "2Ks", "6Qs", "9To", "7Js", "3Ko", "3Qs", "4Qs", "8Ts", "4Ko", "8Jo", "6Qo", "6Js", "2Qs", "7Qo", "89s", "22", "2Ko", "7Ts",
    "5Js", "8To", "4Js", "5Qo", "7Jo", "4Qo", "79s", "6Ts", "3Qo", "7To", "3Js", "6Jo", "89o", "5Jo", "2Js", "69s", "5Ts", "2Qo", "78s", "68s", "79o", "4Ts", "6To", "4Jo", "3Jo", "59s", "67s", "3Ts",
    "2Ts", "2Jo", "78o", "58s", "5To", "69o", "49s", "57s", "39s", "4To", "48s", "29s", "56s", "3To", "68o", "59o", "67o", "47s", "45s", "58o", "2To", "49o", "38s", "57o", "39o", "46s", "35s", "28s", "37s", "29o", "56o", "34s", "36s", "48o", "47o", "45o", "46o", "27s", "25s", "26s", "24s", "37o", "28o", "38o", "36o", "35o", "34o", "23s", "27o", "25o", "26o", "24o", "23o",
]

# Rank 1-169 -> tier name
def _rank_to_tier(rank: int) -> str:
    if rank <= 30:
        return "Premium"
    if rank <= 60:
        return "Strong"
    if rank <= 87:
        return "Playable"
    if rank <= 116:
        return "Marginal"
    return "Weak"


def _normalize_hand(hand: str) -> str | None:
    """Return standard hand notation (as in HAND_RANK_LIST) or None if unknown."""
    h = hand.strip()
    if h in HAND_RANK_LIST:
        return h
    # Map common input "AKs"/"AKo" to list form "KAs"/"KAo" (document uses high card first)
    key = h.replace("-", " ").replace("  ", " ").lower()
    aliases = {
        "ace king suited": "KAs", "ace-king suited": "KAs", "aks": "KAs",
        "ace king offsuit": "KAo", "ace-king offsuit": "KAo", "ako": "KAo",
        "pocket aces": "AA", "aces": "AA", "aa": "AA",
        "kings": "KK", "queens": "QQ", "jj": "JJ",
    }
    if key in aliases:
        return aliases[key]
    if h in aliases:
        return aliases[h]
    # Try two-char + s/o (list uses high rank first: KAs not AKs)
    if len(h) >= 2:
        two = (h[0] + h[1]).upper()
        rest = h[2:].strip().lower()
        if two + "s" in HAND_RANK_LIST and rest in ("s", "suit", "suited", ""):
            return two + "s"
        if two + "o" in HAND_RANK_LIST and rest in ("o", "off", "offsuit", ""):
            return two + "o"
        if two in HAND_RANK_LIST and (rest == "" or "pair" in rest):
            return two
    return None


def _get_hand_rank(hand: str) -> int | None:
    """Return 1-based rank (1 = best) or None if unknown."""
    norm = _normalize_hand(hand)
    if norm is None:
        return None
    try:
        return HAND_RANK_LIST.index(norm) + 1
    except ValueError:
        return None


# ---------- Rules (propositional-style: each must hold for playable) ----------

def _rule_position_valid(position: str) -> bool:
    """Rule: position is Button or Big Blind."""
    return position.strip().lower() in ("button", "big blind", "bb", "btn")


def _rule_hand_strong_enough(rank: int, position: str, opponent: str) -> bool:
    """
    Rule: Hand meets minimum strength for position and opponent.
    - Aggressive/Loose: need Strong or better (rank <= 60).
    - Tight: can play Marginal+ (rank <= 116).
    - Passive: Playable+ (rank <= 87).
    - Unknown: Button Playable+ (<=87), BB Strong+ (<=60).
    """
    opp = opponent.strip().lower()
    pos = position.strip().lower()
    if opp in ("aggressive", "loose"):
        return rank <= 60
    if opp == "tight":
        return rank <= 116
    if opp == "passive":
        return rank <= 87
    # Unknown
    if pos in ("button", "btn"):
        return rank <= 87
    return rank <= 60


def _rule_stack_ok(stack_size: int, hand_rank: int) -> bool:
    """Rule: Stack deep enough for this hand. <10 BB: Premium only; <20 BB: Strong+."""
    if stack_size < 10:
        return hand_rank <= 30
    if stack_size < 20:
        return hand_rank <= 60
    return True


def first_order_logic_hand_decider(
    hand: str,
    position: str,
    stack_size: int,
    opponent_tendency: str,
) -> dict:
    """Decide hand playability using propositional logic rules.

    Args:
        hand: Starting hand (e.g., "Ace-King suited", "AA", "AKs").
        position: Position ("Button" or "Big Blind").
        stack_size: Stack size in big blinds (integer).
        opponent_tendency: "Tight", "Loose", "Aggressive", "Passive", or "Unknown".

    Returns:
        Dict with: playable (bool), reason (str), rules_used (list),
        hand_normalized (str | None), hand_rank (int | None), hand_tier (str | None).
    """
    rules_used: list[str] = []

    if not _rule_position_valid(position):
        return {
            "playable": False,
            "reason": "Invalid position; must be Button or Big Blind.",
            "rules_used": ["position must be Button or Big Blind"],
            "hand_normalized": _normalize_hand(hand),
            "hand_rank": None,
            "hand_tier": None,
        }
    rules_used.append("position is Button or Big Blind")

    hand_rank = _get_hand_rank(hand)
    if hand_rank is None:
        return {
            "playable": False,
            "reason": "Unrecognized hand; cannot evaluate.",
            "rules_used": rules_used,
            "hand_normalized": None,
            "hand_rank": None,
            "hand_tier": None,
        }
    hand_norm = _normalize_hand(hand) or hand
    hand_tier = _rank_to_tier(hand_rank)
    rules_used.append(f"hand strength = {hand_tier} (rank {hand_rank}/169)")

    if not _rule_hand_strong_enough(hand_rank, position, opponent_tendency):
        return {
            "playable": False,
            "reason": f"Hand {hand_norm} ({hand_tier}) is too weak for {position} vs {opponent_tendency}.",
            "rules_used": rules_used,
            "hand_normalized": hand_norm,
            "hand_rank": hand_rank,
            "hand_tier": hand_tier,
        }
    rules_used.append("hand meets minimum strength for position and opponent")

    if not _rule_stack_ok(stack_size, hand_rank):
        return {
            "playable": False,
            "reason": f"Stack too short ({stack_size} BB) for {hand_norm} ({hand_tier}).",
            "rules_used": rules_used,
            "hand_normalized": hand_norm,
            "hand_rank": hand_rank,
            "hand_tier": hand_tier,
        }
    rules_used.append("stack size sufficient for hand strength")

    return {
        "playable": True,
        "reason": f"Play {hand_norm}: {hand_tier} hand, {position}, {stack_size} BB vs {opponent_tendency}.",
        "rules_used": rules_used,
        "hand_normalized": hand_norm,
        "hand_rank": hand_rank,
        "hand_tier": hand_tier,
    }
