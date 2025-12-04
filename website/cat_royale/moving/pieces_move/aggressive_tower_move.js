// Aggressive tower misc helpers (death, state cleanup)
(function() {
    function handleAggressiveTowerDeath(entry) {
        if (!entry) return;
        entry.attack = false;
        entry.aggressive_tower_lived = false;
        if (entry._attackInterval) {
            clearInterval(entry._attackInterval);
            entry._attackInterval = null;
        }
        if (entry._firstAttackTimeout) {
            clearTimeout(entry._firstAttackTimeout);
            entry._firstAttackTimeout = null;
        }
        if (entry.element) {
            const img = entry.element.querySelector('img');
            if (img) {
                // Only set cooked image if hp is actually 0 or below
                const currentHp = entry.hp ?? entry.maxHP ?? 1;
                if (currentHp <= 0) {
                    img.src = '../pieces/agressive_tower/cooked_aggressive_tower.png';
                    img.style.filter = 'grayscale(1)';
                    entry.boardImagePath = '../pieces/agressive_tower/cooked_aggressive_tower.png';
                } else {
                    // Reset to alive state with correct allegiance sprite
                    const towerSpriteFor = window.towerSpriteFor || ((type, allegiance) => {
                        if (allegiance === 'a') {
                            if (type === 'aggressive' || type === 'aggressive_tower') return '../pieces/agressive_tower/aggressive_tower_a.png';
                        }
                        return '../pieces/agressive_tower/aggressive_tower.png';
                    });
                    const aliveSprite = towerSpriteFor('aggressive', entry.allegiance || 'a');
                    img.src = aliveSprite;
                    img.style.filter = '';
                    entry.boardImagePath = aliveSprite;
                }
            }
            entry.element.classList.remove('tower-attack-circle');
        }
    }

    window.handleAggressiveTowerDeath = handleAggressiveTowerDeath;
})();
