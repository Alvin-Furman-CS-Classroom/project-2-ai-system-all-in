# Simple Poker Frontend

A straightforward web interface to play heads-up pre-flop poker against the AI agent.

## Features

- **Auto-start**: Game begins immediately when page loads
- **Default settings**: 50 BB each, AI assumes "Unknown" opponent type
- **AI Integration**: Uses Module 1 (Propositional Logic) and Module 2 (A* Search)
- **Simple UI**: Clean, functional interface

## Setup

1. **Install Flask**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the server**:
   ```bash
   python app.py
   ```

3. **Open browser**:
   Navigate to `http://localhost:5001`

## How to Play

1. **Page loads** → Game starts automatically
2. **See your cards** → Make your decision (Fold/Call/Raise)
3. **AI responds** → See AI's decision and reasoning
4. **Showdown** → If both call, cards are revealed
5. **New Hand** → Click "New Hand" button to play again

## File Structure

```
poker_frontend/
├── app.py                 # Flask backend
├── requirements.txt       # Flask dependency
├── templates/
│   └── index.html        # Main game page
└── static/
    ├── css/
    │   └── style.css     # Styling
    └── js/
        ├── api.js        # API calls
        ├── cards.js      # Card rendering
        └── game.js       # Game logic
```

## API Endpoints

- `POST /api/new_game` - Start new game (auto-starts with defaults)
- `POST /api/player_action` - Player makes action
- `POST /api/ai_action` - Get AI decision
- `POST /api/showdown` - Resolve showdown

## Troubleshooting

**Port 5001 already in use?**
- Edit `app.py` and change `port=5001` to another port

**Module import errors?**
- Make sure you're running from the project root
- Check that Module 1 and Module 2 directories exist

**Game not starting?**
- Check browser console (F12) for errors
- Check server terminal for Python errors
