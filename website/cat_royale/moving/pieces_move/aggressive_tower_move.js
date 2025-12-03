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
                img.src = '../pieces/agressive_tower/cooked_aggressive_tower.png';
                img.style.filter = 'grayscale(1)';
            }
            entry.element.classList.remove('tower-attack-circle');
        }
    }

    window.handleAggressiveTowerDeath = handleAggressiveTowerDeath;
})();
