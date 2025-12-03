// Ruler ability: if elixir>=2, not in ability/move cooldown, and a troop target is in range,
// clicking the second-from-bottom ability button starts attacking the nearest troop.
(function() {
    const ABILITY_COST = 2;
    const ABILITY_COOLDOWN_MS = 5000;

    function getPlayerRuler() {
        if (!window.pieceDeployment) return null;
        return (pieceDeployment.boardPieces || []).find(p =>
            p.type === 'ruler' &&
            p.allegiance === 'a' &&
            (p.hp ?? p.maxHP ?? 0) > 0
        );
    }

    function getMoveCooldownRemaining(rulerEntry) {
        const last = rulerEntry?._mover?.lastMoveAt || 0;
        const MOVE_COOLDOWN_MS = 5000;
        const elapsed = Date.now() - last;
        return Math.max(0, MOVE_COOLDOWN_MS - elapsed);
    }

    function findNearestTroopInRange(ruler) {
        if (!ruler || !window.isRulerInRange) return null;
        const troops = (pieceDeployment.boardPieces || []).filter(p =>
            p.role === 'troop' &&
            p.allegiance !== ruler.allegiance &&
            (p.hp ?? 0) > 0 &&
            window.isRulerInRange(ruler, p)
        );
        if (troops.length === 0) return null;
        const { row: sr, col: sc } = ruler.position || {};
        let best = null;
        let bestDist = Infinity;
        troops.forEach(p => {
            const d = Math.abs((p.position?.row ?? 0) - sr) + Math.abs((p.position?.col ?? 0) - sc);
            if (d < bestDist) {
                bestDist = d;
                best = p;
            }
        });
        return best;
    }

    function init(options = {}) {
        const button = options.button;
        if (!button) return;
        let abilityCooldownUntil = 0;

        button.addEventListener('click', (e) => {
            e.stopPropagation();
            const ruler = getPlayerRuler();
            if (!ruler) return;
            if (!window.startRulerAttack || !window.isRulerInRange) return;
            if (Date.now() < abilityCooldownUntil) return;
            if (elixirManager?.currentElixir < ABILITY_COST) return;
            if (getMoveCooldownRemaining(ruler) > 0) return;

            const target = findNearestTroopInRange(ruler);
            if (!target) return;

            // Spend elixir
            elixirManager.currentElixir -= ABILITY_COST;
            elixirManager.updateElixirDisplay();
            elixirManager.updateElixirBar();
            elixirManager.startElixirGeneration();

            abilityCooldownUntil = Date.now() + ABILITY_COOLDOWN_MS;
            window.startRulerAttack(ruler, target);
        });
    }

    window.RulerAbility = { init };
})();
