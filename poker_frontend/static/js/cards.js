/**
 * Card rendering utilities - Simple text-based cards
 */

function renderHand(containerId, handStr, faceDown = false) {
    try {
        const container = document.getElementById(containerId);
        if (!container) {
            console.warn(`Hand container not found: ${containerId}`);
            return;
        }
        
        if (faceDown || !handStr || handStr === '??') {
            container.textContent = '??';
            container.className = 'hand face-down';
        } else {
            container.textContent = handStr;
            container.className = 'hand';
        }
    } catch (error) {
        console.error(`Error rendering hand in ${containerId}:`, error);
        const container = document.getElementById(containerId);
        if (container) {
            container.textContent = handStr || '??';
        }
    }
}

function revealCard(containerId, handStr) {
    try {
        const container = document.getElementById(containerId);
        if (!container) {
            console.warn(`Reveal container not found: ${containerId}`);
            return;
        }
        
        // Simple reveal - just show the hand
        container.textContent = handStr;
        container.classList.remove('face-down');
        container.classList.add('hand');
    } catch (error) {
        console.error(`Error revealing cards in ${containerId}:`, error);
    }
}
