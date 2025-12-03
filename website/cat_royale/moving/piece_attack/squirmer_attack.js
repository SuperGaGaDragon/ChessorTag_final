// Squirmer attack: adjacent orthogonal only; rams target every 1.7s for 80 damage.
(function() {
    const DAMAGE = 80;
    const INTERVAL_MS = 1700;

    function isSquirmerAttackInRange(attacker, target) {
        if (!attacker || !target || !target.position) return false;
        if (target.role !== 'building') return false;
        const dr = Math.abs((attacker.position?.row ?? 0) - target.position.row);
        const dc = Math.abs((attacker.position?.col ?? 0) - target.position.col);
        return (dr + dc === 1); // orthogonally adjacent only
    }

    function startSquirmerAttack(attacker, target) {
        if (!attacker || attacker.shouter_lived === false || (attacker.hp !== undefined && attacker.hp <= 0)) return;
        if (attacker.attack && attacker._attackInterval && attacker.currentTargetId === (target && target.id)) {
            return;
        }
        attacker.attack = true;
        attacker.currentTargetId = target?.id || null;

        if (attacker._attackInterval) clearInterval(attacker._attackInterval);

        const doRam = () => {
            if (!attacker.attack || (attacker.hp !== undefined && attacker.hp <= 0)) return false;
            if (!target || target.role !== 'building' || (target.hp !== undefined && target.hp <= 0)) {
                attacker.attack = false;
                attacker.currentTargetId = null;
                return false;
            }
            if (!isSquirmerAttackInRange(attacker, target)) {
                attacker.attack = false;
                attacker.currentTargetId = null;
                return false;
            }

            const attackerEl = attacker.element || document.querySelector(`.board-cell[data-row="${attacker.position?.row}"][data-col="${attacker.position?.col}"]`);
            const targetEl = target.element || document.querySelector(`.board-cell[data-row="${target.position?.row}"][data.col="${target.position?.col}"]`) || document.querySelector(`.board-cell[data-row="${target.position?.row}"][data-col="${target.position?.col}"]`);
            if (attackerEl && targetEl && attackerEl.animate) {
                const aRect = attackerEl.getBoundingClientRect();
                const tRect = targetEl.getBoundingClientRect();
                const dx = (tRect.left + tRect.width / 2) - (aRect.left + aRect.width / 2);
                const dy = (tRect.top + tRect.height / 2) - (aRect.top + aRect.height / 2);
                const bumpX = dx * 0.25;
                const bumpY = dy * 0.25;
                attackerEl.animate([
                    { transform: 'translate(0,0)' },
                    { transform: `translate(${bumpX}px, ${bumpY}px)` },
                    { transform: 'translate(0,0)' }
                ], {
                    duration: 500,
                    easing: 'ease-in-out',
                    fill: 'none'
                });
            }

            if (window.pieceDeployment) window.pieceDeployment.applyDamage(target, DAMAGE, attacker);
            return true;
        };

        // Hit immediately then at interval
        doRam();
        attacker._attackInterval = setInterval(() => {
            if (!doRam()) {
                clearInterval(attacker._attackInterval);
                attacker._attackInterval = null;
            }
        }, INTERVAL_MS);
    }

    function stopSquirmerAttack(attacker) {
        if (!attacker) return;
        attacker.attack = false;
        attacker.currentTargetId = null;
        if (attacker._attackInterval) {
            clearInterval(attacker._attackInterval);
            attacker._attackInterval = null;
        }
    }

    window.isSquirmerAttackInRange = isSquirmerAttackInRange;
    window.startSquirmerAttack = startSquirmerAttack;
    window.stopSquirmerAttack = stopSquirmerAttack;
})();
