"""
Flask backend for Simple Poker Frontend.

Auto-starts games with 50 BB each, "Unknown" opponent type.
"""

from flask import Flask, render_template, request, jsonify
import sys
from pathlib import Path
import random

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent.parent / "Module 1"))
sys.path.insert(0, str(Path(__file__).parent.parent / "Module 2"))
sys.path.insert(0, str(Path(__file__).parent.parent / "Module 2"))

from propositional_logic import propositional_logic_hand_decider
from bet_sizing_search import a_star_search
from ev_calculator import get_hand_equity

app = Flask(__name__)

# All 169 possible starting hands
ALL_HANDS = [
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "KAs", "QAs", "JAs", "KAo", "QAo", "TAs", "66", "JAo", "QKs", "9As", "TAo", "JKs", "8As", "TKs", "5As", "QKo", "9Ao", "JKo", "7As", "TKo", "JQs", "6As",
    "8Ao", "4As", "55", "9Ks", "3As", "6Ao", "8Ks", "TQs", "JQo", "2As", "9Ko", "9Qs", "TJs", "7Ks", "5Ao", "4Ao", "7Ao", "6Ks", "44", "TQo", "7Ko", "3Ao", "9Qo", "8Qs", "8Ko", "9Js", "TJo", "5Ks", "2Ao", "6Ko",
    "4Ks", "33", "8Js", "7Qs", "9Jo", "5Ko", "3Ks", "8Qo", "9Ts", "5Qs", "2Ks", "6Qs", "9To", "7Js", "3Ko", "3Qs", "4Qs", "8Ts", "4Ko", "8Jo", "6Qo", "6Js", "2Qs", "7Qo", "89s", "22", "2Ko", "7Ts",
    "5Js", "8To", "4Js", "5Qo", "7Jo", "4Qo", "79s", "6Ts", "3Qo", "7To", "3Js", "6Jo", "89o", "5Jo", "2Js", "69s", "5Ts", "2Qo", "78s", "68s", "79o", "4Ts", "6To", "4Jo", "3Jo", "59s", "67s", "3Ts",
    "2Ts", "2Jo", "78o", "58s", "5To", "69o", "49s", "57s", "39s", "4To", "48s", "29s", "56s", "3To", "68o", "59o", "67o", "47s", "45s", "58o", "2To", "49o", "38s", "57o", "39o", "46s", "35s", "28s", "37s", "29o", "56o", "34s", "36s", "48o", "47o", "45o", "46o", "27s", "25s", "26s", "24s", "37o", "28o", "38o", "36o", "35o", "34o", "23s", "27o", "25o", "26o", "24o", "23o",
]

# Game state storage (in-memory, single session)
games = {}


def deal_hands():
    """Deal two random hands (no overlap)."""
    hand1 = random.choice(ALL_HANDS)
    hand2 = random.choice([h for h in ALL_HANDS if h != hand1])
    return hand1, hand2


@app.route('/')
def index():
    """Main game page."""
    return render_template('index.html')


@app.route('/api/new_game', methods=['POST'])
def new_game():
    """Start a new game with defaults: 50 BB each, "Unknown" opponent type."""
    # Default values
    player_stack = 50
    ai_stack = 50
    ai_tendency = "Unknown"
    
    # Deal hands
    player_hand, ai_hand = deal_hands()
    
    # Determine who is Button (random)
    player_is_button = random.choice([True, False])
    
    game_id = f"game_{random.randint(1000, 9999)}"
    games[game_id] = {
        'player_hand': player_hand,
        'ai_hand': ai_hand,
        'player_stack': player_stack,
        'ai_stack': ai_stack,
        'player_is_button': player_is_button,
        'ai_tendency': ai_tendency,
        'pot': 1.5,  # Blinds
        'player_invested': 0.5 if player_is_button else 1.0,  # SB or BB
        'ai_invested': 1.0 if player_is_button else 0.5,
        'current_bet': 0.0,  # Amount to call
        'last_bettor': None,  # "player" or "ai"
        'action_history': [],
        'game_over': False,
        'winner': None,
    }
    
    return jsonify({
        'game_id': game_id,
        'player_hand': player_hand,
        'player_is_button': player_is_button,
        'player_stack': player_stack,
        'ai_stack': ai_stack,
        'pot': 1.5,
        'current_bet': 1.0 if player_is_button else 0.0,  # Button needs to call BB (1.0), BB has already posted
    })


@app.route('/api/ai_action', methods=['POST'])
def ai_action():
    """Get AI's action using Module 1 and Module 2."""
    data = request.json
    game_id = data.get('game_id')
    
    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404
    
    game = games[game_id]
    
    # Determine AI's position
    ai_position = "Button" if not game['player_is_button'] else "Big Blind"
    
    # Get AI decision using Module 1 and Module 2
    # First check if hand is playable (Module 1)
    module1_result = propositional_logic_hand_decider(
        game['ai_hand'],
        ai_position,
        game['ai_stack'],
        game['ai_tendency']
    )
    
    if not module1_result.get('playable', False):
        action = "fold"
        bet_size = 0.0
        ev = 0.0
        reason = module1_result.get('reason', 'Hand not playable')
    else:
        # Use Module 2 to get optimal bet size
        opponent_bet = game['current_bet'] if game['last_bettor'] == 'player' else None
        module2_result = a_star_search(
            game['ai_hand'],
            ai_position,
            (game['ai_stack'], game['player_stack']),
            game['ai_tendency'],
            opponent_bet_size=opponent_bet,
            pot_size=game['pot']
        )
        action = module2_result['action']
        bet_size = module2_result['bet_size']
        ev = module2_result['ev']
        reason = f"AI {action}s {bet_size:.1f}x BB (EV: {ev:.2f} BB)"
    
    # Update game state based on AI action
    if action == "fold":
        game['game_over'] = True
        game['winner'] = "player"
    elif action == "call":
        call_amount = game['current_bet'] - game['ai_invested']
        game['ai_invested'] += call_amount
        game['pot'] += call_amount
        game['ai_stack'] -= call_amount
        # Check if both players matched bets
        if abs(game['player_invested'] - game['ai_invested']) < 0.01:
            game['game_over'] = True
            game['winner'] = "showdown"
    elif action == "raise":
        raise_amount = bet_size - game['ai_invested']
        game['ai_invested'] = bet_size
        game['pot'] += raise_amount
        game['ai_stack'] -= raise_amount
        game['current_bet'] = bet_size
        game['last_bettor'] = 'ai'
    
    return jsonify({
        'action': action,
        'bet_size': bet_size,
        'ev': ev,
        'reason': reason,
        'module1_result': module1_result,
        'module2_result': module2_result if action != "fold" else None,
        'game_over': game.get('game_over', False),
        'winner': game.get('winner'),
        'pot': game['pot'],
        'ai_stack': game['ai_stack'],
        'ai_invested': game['ai_invested'],
        'current_bet': game['current_bet'],
    })


@app.route('/api/player_action', methods=['POST'])
def player_action():
    """Process player's action and update game state."""
    data = request.json
    game_id = data.get('game_id')
    action = data.get('action')  # "fold", "call", "raise"
    bet_size = data.get('bet_size', 0.0)
    
    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404
    
    game = games[game_id]
    
    if game['game_over']:
        return jsonify({'error': 'Game already over'}), 400
    
    # Process player action
    if action == "fold":
        game['game_over'] = True
        game['winner'] = "ai"
        return jsonify({
            'game_over': True,
            'winner': 'ai',
            'message': 'You folded. AI wins!'
        })
    
    elif action == "call":
        call_amount = game['current_bet'] - game['player_invested']
        game['player_invested'] += call_amount
        game['pot'] += call_amount
        game['player_stack'] -= call_amount
        
        # If both players have matched bets, go to showdown
        if abs(game['player_invested'] - game['ai_invested']) < 0.01:
            return jsonify({
                'game_over': True,
                'winner': 'showdown',
                'message': 'Both players called. Showdown!',
                'player_hand': game['player_hand'],
                'ai_hand': game['ai_hand'],
                'pot': game['pot'],
                'player_stack': game['player_stack'],
                'player_invested': game['player_invested'],
            })
        
        # Otherwise, it's AI's turn
        return jsonify({
            'game_over': False,
            'message': 'You called. AI to act...',
            'pot': game['pot'],
            'player_stack': game['player_stack'],
            'player_invested': game['player_invested'],
            'current_bet': game['current_bet'],
        })
    
    elif action == "raise":
        raise_amount = bet_size - game['player_invested']
        game['player_invested'] = bet_size
        game['pot'] += raise_amount
        game['player_stack'] -= raise_amount
        game['current_bet'] = bet_size
        game['last_bettor'] = 'player'
        
        return jsonify({
            'game_over': False,
            'message': f'You raised to {bet_size:.1f}x BB. AI to act...',
            'pot': game['pot'],
            'current_bet': game['current_bet'],
            'player_stack': game['player_stack'],
            'player_invested': game['player_invested'],
        })
    
    return jsonify({'error': 'Invalid action'}), 400


@app.route('/api/showdown', methods=['POST'])
def showdown():
    """Calculate showdown winner based on hand equity."""
    data = request.json
    game_id = data.get('game_id')
    
    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404
    
    game = games[game_id]
    
    # Get hand equities (simplified - use pre-flop equity)
    player_equity = get_hand_equity(game['player_hand'])
    ai_equity = get_hand_equity(game['ai_hand'])
    
    # Determine winner (simplified - higher equity wins)
    if player_equity > ai_equity:
        winner = "player"
        message = f"You win! ({player_equity:.1%} vs {ai_equity:.1%})"
    elif ai_equity > player_equity:
        winner = "ai"
        message = f"AI wins! ({ai_equity:.1%} vs {player_equity:.1%})"
    else:
        winner = "tie"
        message = "It's a tie!"
    
    game['game_over'] = True
    game['winner'] = winner
    
    return jsonify({
        'winner': winner,
        'message': message,
        'player_hand': game['player_hand'],
        'ai_hand': game['ai_hand'],
        'player_equity': player_equity,
        'ai_equity': ai_equity,
        'pot': game['pot'],
    })


if __name__ == '__main__':
    app.run(debug=True, port=5001)
