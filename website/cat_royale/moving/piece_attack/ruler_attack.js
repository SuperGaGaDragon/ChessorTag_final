// Ruler attack: attacks troops within its quarter of the board.
(function() {
    const DAMAGE = 40;
    const INTERVAL_MS = 1000;

    function isInQuarter(attacker, target) {
        if (!attacker?.position || !target?.position) return false;
        const myRowTop = attacker.position.row <= 3;
        const myColLeft = attacker.position.col <= 3;
        const rowOk = myRowTop ? target.position.row <= 3 : target.position.row >= 4;
        const colOk = myColLeft ? target.position.col <= 3 : target.position.col >= 4;
        return rowOk && colOk;
    }

    function isRulerInRange(attacker, target) {
        if (!attacker || !target) return false;
        if (target.role !== 'troop') return false;
        return isInQuarter(attacker, target);
    }

    function startRulerAttack(attacker, target) {
        if (!attacker || (attacker.hp !== undefined && attacker.hp <= 0)) return;
        if (!target || target.role !== 'troop' || (target.hp !== undefined && target.hp <= 0)) return;
        if (!isRulerInRange(attacker, target)) return;
        if (attacker.attack && attacker._attackInterval && attacker.currentTargetId === (target && target.id)) {
            return;
        }
        attacker.attack = true;
        attacker.currentTargetId = target?.id || null;

        if (attacker._attackInterval) clearInterval(attacker._attackInterval);

        const swing = () => {
            if (!attacker.attack || (attacker.hp !== undefined && attacker.hp <= 0)) return false;
            if (!target || target.role !== 'troop' || (target.hp !== undefined && target.hp <= 0)) {
                attacker.attack = false;
                attacker.currentTargetId = null;
                return false;
            }
            if (!isRulerInRange(attacker, target)) {
                attacker.attack = false;
                attacker.currentTargetId = null;
                return false;
            }
            if (window.pieceDeployment) window.pieceDeployment.applyDamage(target, DAMAGE, attacker);
            return true;
        };

        // Hit once immediately
        swing();
        attacker._attackInterval = setInterval(() => {
            if (!swing()) {
                clearInterval(attacker._attackInterval);
                attacker._attackInterval = null;
            }
        }, INTERVAL_MS);
    }

    function stopRulerAttack(attacker) {
        if (!attacker) return;
        attacker.attack = false;
        attacker.currentTargetId = null;
        if (attacker._attackInterval) {
            clearInterval(attacker._attackInterval);
            attacker._attackInterval = null;
        }
    }

    window.isRulerInRange = isRulerInRange;
    window.startRulerAttack = startRulerAttack;
    window.stopRulerAttack = stopRulerAttack;
})();
