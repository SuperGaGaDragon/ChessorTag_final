// Solid tower misc helpers (death, state cleanup)
(function() {
    function handleSolidTowerDeath(entry) {
        if (!entry) return;
        entry.attack = false;
        entry.solid_tower_lived = false;
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
                    img.src = '../pieces/solid_tower/cooked_solid_tower.png';
                    img.style.filter = 'grayscale(1)';
                    entry.boardImagePath = '../pieces/solid_tower/cooked_solid_tower.png';
                } else {
                    // Reset to alive state with correct allegiance sprite
                    const towerSpriteFor = window.towerSpriteFor || ((type, allegiance) => {
                        if (allegiance === 'a') {
                            if (type === 'solid' || type === 'solid_tower') return '../pieces/solid_tower/solid_tower_a.png';
                        }
                        return '../pieces/solid_tower/solid_tower.png';
                    });
                    const aliveSprite = towerSpriteFor('solid', entry.allegiance || 'a');
                    img.src = aliveSprite;
                    img.style.filter = '';
                    entry.boardImagePath = aliveSprite;
                }
            }
            entry.element.classList.remove('tower-attack-circle');
        }
    }

    window.handleSolidTowerDeath = handleSolidTowerDeath;
})();
