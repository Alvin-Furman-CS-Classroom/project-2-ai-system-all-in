/**
 * API Communication - Simple fetch functions
 */

const API_BASE = '/api';

async function newGame() {
    // Auto-start with defaults: 50 BB each, "Unknown" opponent type
    const response = await fetch(`${API_BASE}/new_game`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})  // Empty body - uses defaults
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

async function playerAction(gameId, action, betSize) {
    const response = await fetch(`${API_BASE}/player_action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            game_id: gameId, 
            action: action, 
            bet_size: betSize 
        })
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

async function getAIAction(gameId) {
    const response = await fetch(`${API_BASE}/ai_action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ game_id: gameId })
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

async function showdown(gameId) {
    const response = await fetch(`${API_BASE}/showdown`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ game_id: gameId })
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}
