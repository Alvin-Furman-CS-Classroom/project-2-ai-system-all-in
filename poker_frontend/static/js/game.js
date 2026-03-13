/**
 * Game Logic - Main game state management
 */

// Game state
let gameState = {
    gameId: null,
    playerHand: null,
    playerIsButton: null,
    playerStack: 50,
    aiStack: 50,
    pot: 1.5,
    currentBet: 0,
    waitingForAI: false,
    playerInvested: 0,
    aiInvested: 0,
};

// DOM Elements
let foldBtn, callBtn, raiseBtn, raiseSizeInput, newHandBtn, aiDecision, statusDiv;

// Initialize - game starts automatically when page loads
window.addEventListener('DOMContentLoaded', () => {
    // Get DOM elements
    foldBtn = document.getElementById('fold');
    callBtn = document.getElementById('call');
    raiseBtn = document.getElementById('raise');
    raiseSizeInput = document.getElementById('raise_size');
    newHandBtn = document.getElementById('new_hand');
    aiDecision = document.getElementById('ai_decision');
    statusDiv = document.getElementById('status');

    // Event listeners
    if (foldBtn) foldBtn.addEventListener('click', () => makePlayerAction('fold'));
    if (callBtn) callBtn.addEventListener('click', () => makePlayerAction('call'));
    if (raiseBtn) {
        raiseBtn.addEventListener('click', () => {
            const betSize = parseFloat(raiseSizeInput.value);
            if (isNaN(betSize) || betSize < 2.0) {
                alert('Please enter a valid bet size (minimum 2.0 BB)');
                return;
            }
            makePlayerAction('raise', betSize);
        });
    }
    if (newHandBtn) newHandBtn.addEventListener('click', startGame);

    // Start game automatically
    startGame();
});

async function startGame() {
    try {
        // Auto-start with defaults: 50 BB each, "Unknown" opponent type
        const data = await newGame();
        gameState = {
            gameId: data.game_id,
            playerHand: data.player_hand,
            playerIsButton: data.player_is_button,
            playerStack: data.player_stack,
            aiStack: data.ai_stack,
            pot: data.pot,
            currentBet: data.current_bet,
            waitingForAI: false,
            playerInvested: data.player_is_button ? 0.5 : 1.0,
            aiInvested: data.player_is_button ? 1.0 : 0.5,
        };

        updateDisplay();
        
        // Hide status and new hand button
        if (statusDiv) statusDiv.classList.add('hidden');
        if (newHandBtn) newHandBtn.classList.add('hidden');
        if (aiDecision) aiDecision.classList.add('hidden');
        
        enableActions();

        // If AI acts first (player is Big Blind)
        if (!gameState.playerIsButton) {
            await aiTurn();
        }
    } catch (error) {
        console.error('Error starting game:', error);
        showStatus('Failed to start game. Please refresh the page.', 'info');
    }
}

function updateDisplay() {
    try {
        // Update positions
        const playerPos = gameState.playerIsButton ? 'Button' : 'Big Blind';
        const aiPos = gameState.playerIsButton ? 'Big Blind' : 'Button';
        const playerPosEl = document.getElementById('player_position');
        const aiPosEl = document.getElementById('ai_position');
        if (playerPosEl) playerPosEl.textContent = playerPos;
        if (aiPosEl) aiPosEl.textContent = aiPos;

        // Render cards
        renderHand('player_hand', gameState.playerHand, false);
        renderHand('ai_hand', null, true); // Face down until showdown

        // Update stacks
        const playerStackEl = document.getElementById('player_stack_display');
        const aiStackEl = document.getElementById('ai_stack_display');
        if (playerStackEl) playerStackEl.textContent = gameState.playerStack.toFixed(1);
        if (aiStackEl) aiStackEl.textContent = gameState.aiStack.toFixed(1);

        // Update invested amounts
        const playerInvestedEl = document.getElementById('player_invested_display');
        const aiInvestedEl = document.getElementById('ai_invested_display');
        if (playerInvestedEl) playerInvestedEl.textContent = gameState.playerInvested.toFixed(1);
        if (aiInvestedEl) aiInvestedEl.textContent = gameState.aiInvested.toFixed(1);

        // Update pot and bet
        const potEl = document.getElementById('pot_display');
        const betEl = document.getElementById('current_bet_display');
        if (potEl) potEl.textContent = gameState.pot.toFixed(1);
        if (betEl) betEl.textContent = gameState.currentBet.toFixed(1);

        // Update call amount
        const callAmount = Math.max(0, gameState.currentBet - gameState.playerInvested);
        if (callBtn) {
            if (callAmount === 0) {
                callBtn.textContent = 'Check';
            } else {
                callBtn.textContent = `Call ${callAmount.toFixed(1)} BB`;
            }
        }
    } catch (error) {
        console.error('Error updating display:', error);
    }
}

async function makePlayerAction(action, betSize = null) {
    if (gameState.waitingForAI || !gameState.gameId) return;

    try {
        disableActions();
        const data = await playerAction(gameState.gameId, action, betSize);

        if (data.error) {
            alert(data.error);
            enableActions();
            return;
        }

        if (data.game_over) {
            if (data.winner === 'showdown') {
                await handleShowdown();
            } else if (data.winner === 'ai') {
                showStatus('You folded. AI wins!', 'lose');
                if (newHandBtn) newHandBtn.classList.remove('hidden');
            } else {
                showStatus('You win!', 'win');
                if (newHandBtn) newHandBtn.classList.remove('hidden');
            }
        } else {
            // Update game state
            if (data.pot !== undefined) gameState.pot = data.pot;
            if (data.player_stack !== undefined) gameState.playerStack = data.player_stack;
            if (data.current_bet !== undefined) gameState.currentBet = data.current_bet;
            if (data.player_invested !== undefined) gameState.playerInvested = data.player_invested;

            updateDisplay();
            showStatus(data.message || 'Your turn', 'info');
            
            // AI's turn
            await aiTurn();
        }
    } catch (error) {
        console.error('Error performing action:', error);
        alert('Failed to perform action. Please try again.');
        enableActions();
    }
}

async function aiTurn() {
    gameState.waitingForAI = true;
    disableActions();
    
    if (aiDecision) {
        aiDecision.classList.remove('hidden');
        const aiActionText = document.getElementById('ai_action_text');
        if (aiActionText) {
            aiActionText.innerHTML = '<p>🤖 AI is thinking...</p>';
        }
    }

    try {
        const data = await getAIAction(gameState.gameId);
        
        // Display AI action
        if (aiDecision) {
            aiDecision.classList.remove('hidden');
            const aiActionText = document.getElementById('ai_action_text');
            if (aiActionText) {
                let html = `
                    <p><strong>Action:</strong> ${data.action.toUpperCase()}</p>
                    <p><strong>Bet Size:</strong> ${data.bet_size.toFixed(1)}x BB</p>
                    <p><strong>Expected Value:</strong> ${data.ev.toFixed(2)} BB</p>
                    <p><strong>Reason:</strong> ${data.reason}</p>
                `;
                
                if (data.module1_result) {
                    html += `
                        <details>
                            <summary>Module 1 Reasoning (Propositional Logic)</summary>
                            <pre>${JSON.stringify(data.module1_result, null, 2)}</pre>
                        </details>
                    `;
                }
                
                if (data.module2_result) {
                    html += `
                        <details>
                            <summary>Module 2 Analysis (A* Search)</summary>
                            <pre>${JSON.stringify(data.module2_result, null, 2)}</pre>
                        </details>
                    `;
                }
                
                aiActionText.innerHTML = html;
            }
        }

        // Simulate AI thinking delay
        await new Promise(resolve => setTimeout(resolve, 1500));

        // Update game state from response
        if (data.pot !== undefined) gameState.pot = data.pot;
        if (data.ai_stack !== undefined) gameState.aiStack = data.ai_stack;
        if (data.current_bet !== undefined) gameState.currentBet = data.current_bet;
        if (data.ai_invested !== undefined) gameState.aiInvested = data.ai_invested;

        if (data.game_over) {
            if (data.winner === 'showdown') {
                updateDisplay();
                await handleShowdown();
            } else if (data.winner === 'player') {
                showStatus('AI folded. You win!', 'win');
                if (newHandBtn) newHandBtn.classList.remove('hidden');
            } else {
                showStatus('AI wins!', 'lose');
                if (newHandBtn) newHandBtn.classList.remove('hidden');
            }
        } else if (data.action === 'fold') {
            showStatus('AI folded. You win!', 'win');
            if (newHandBtn) newHandBtn.classList.remove('hidden');
        } else if (data.action === 'call') {
            // Both players called - showdown
            updateDisplay();
            await handleShowdown();
        } else if (data.action === 'raise') {
            // AI raised - update game state and wait for player
            updateDisplay();
            showStatus(`AI raised to ${data.bet_size.toFixed(1)}x BB. Your turn.`, 'info');
            enableActions();
        }
    } catch (error) {
        console.error('Error getting AI action:', error);
        alert('Failed to get AI action. Please try again.');
        enableActions();
    } finally {
        gameState.waitingForAI = false;
    }
}

async function handleShowdown() {
    try {
        const data = await showdown(gameState.gameId);
        
        // Reveal AI hand
        revealCard('ai_hand', data.ai_hand);
        
        // Wait a moment for reveal
        await new Promise(resolve => setTimeout(resolve, 500));
        
        const message = `
            ${data.message}<br>
            <div style="margin-top: 15px; font-size: 0.9em;">
                Your hand: <strong>${data.player_hand}</strong> (${(data.player_equity * 100).toFixed(1)}%)<br>
                AI hand: <strong>${data.ai_hand}</strong> (${(data.ai_equity * 100).toFixed(1)}%)
            </div>
        `;
        
        if (data.winner === 'player') {
            showStatus(message, 'win');
        } else if (data.winner === 'ai') {
            showStatus(message, 'lose');
        } else {
            showStatus(message, 'info');
        }
        
        if (newHandBtn) newHandBtn.classList.remove('hidden');
    } catch (error) {
        console.error('Error handling showdown:', error);
        alert('Failed to resolve showdown.');
    }
}

function showStatus(message, type) {
    if (statusDiv) {
        statusDiv.innerHTML = message;
        statusDiv.className = `status ${type}`;
        statusDiv.classList.remove('hidden');
    }
}

function disableActions() {
    if (foldBtn) foldBtn.disabled = true;
    if (callBtn) callBtn.disabled = true;
    if (raiseBtn) raiseBtn.disabled = true;
}

function enableActions() {
    if (foldBtn) foldBtn.disabled = false;
    if (callBtn) callBtn.disabled = false;
    if (raiseBtn) raiseBtn.disabled = false;
}
