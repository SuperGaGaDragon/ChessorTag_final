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
                img.src = '../pieces/solid_tower/cooked_solid_tower.png';
                img.style.filter = 'grayscale(1)';
            }
            entry.element.classList.remove('tower-attack-circle');
        }
    }

    window.handleSolidTowerDeath = handleSolidTowerDeath;
})();
