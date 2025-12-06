// Aggressive tower attack: engages troops within 2 tiles (Chebyshev distance).
// When attacking, it circles in place and fires a 🐔 projectile toward the target every ~0.333s.

(function() {
    const INTERVAL_MS = 333;
    const SPEED_MS = 700;
    const DAMAGE = 25;

    ensureCircleStyle();

    function isInQuarter(attacker, target) {
        if (!attacker?.position || !target?.position) return false;
        const myRowTop = attacker.position.row <= 3;
        const myColLeft = attacker.position.col <= 3;
        const rowOk = myRowTop ? target.position.row <= 3 : target.position.row >= 4;
        const colOk = myColLeft ? target.position.col <= 3 : target.position.col >= 4;
        return rowOk && colOk;
    }

    function isAggressiveTowerInRange(attacker, target) {
        if (!attacker || !target || target.role !== 'troop') return false;
        return isInQuarter(attacker, target);
    }

    function startAggressiveTowerAttack(attacker, target, visualOnly = false) {
        if (!attacker || (attacker.hp !== undefined && attacker.hp <= 0) || attacker.aggressive_tower_lived === false) return;
        if (attacker.attack && attacker._attackInterval && attacker.currentTargetId === (target && target.id)) {
            return;
        }
        attacker.attack = true;
        attacker.currentTargetId = target?.id || null;
        applyCircleMotion(getAnchorElement(attacker));

        // Clear any previous interval
        if (attacker._attackInterval) clearInterval(attacker._attackInterval);

        const fire = () => {
            if (!attacker.attack || (attacker.hp !== undefined && attacker.hp <= 0) || attacker.aggressive_tower_lived === false) {
                // 清除动画
                const anchor = getAnchorElement(attacker);
                if (anchor) anchor.classList.remove('tower-attack-circle');
                return false;
            }
            if (!target || target.role !== 'troop' || (target.hp !== undefined && target.hp <= 0)) {
                attacker.attack = false;
                attacker.currentTargetId = null;
                // 清除动画
                const anchor = getAnchorElement(attacker);
                if (anchor) anchor.classList.remove('tower-attack-circle');
                return false;
            }
            if (!isAggressiveTowerInRange(attacker, target)) {
                attacker.attack = false;
                attacker.currentTargetId = null;
                // 清除动画
                const anchor = getAnchorElement(attacker);
                if (anchor) anchor.classList.remove('tower-attack-circle');
                return false;
            }
            const targetEl = getAnchorElement(target);
            const anchor = getAnchorElement(attacker);
            if (!anchor || !targetEl) return false;
            spawnProjectile(anchor, targetEl, '🐔', SPEED_MS, () => {
                // Only apply damage if HOST and not visualOnly mode
                if (!visualOnly && window.IS_HOST === true && window.pieceDeployment) {
                    window.pieceDeployment.applyDamage(target, DAMAGE, attacker);
                }
            });
            return true;
        };

        // Fire immediately, then continue at interval
        fire();
        attacker._attackInterval = setInterval(() => {
            if (!fire()) {
                clearInterval(attacker._attackInterval);
                attacker._attackInterval = null;
            }
        }, INTERVAL_MS);
    }

    function applyCircleMotion(el) {
        if (!el) return;
        el.classList.add('tower-attack-circle');
    }

    function getAnchorElement(piece) {
        if (piece.element) return piece.element;
        const cell = document.querySelector(`.board-cell[data-row="${piece.position?.row}"][data-col="${piece.position?.col}"]`);
        return cell || null;
    }

    function spawnProjectile(fromEl, toEl, content, duration, onHit) {
        const fromRect = fromEl.getBoundingClientRect();
        const toRect = toEl.getBoundingClientRect();
        if (!fromRect || !toRect) return;

        const proj = document.createElement('div');
        proj.textContent = content;
        proj.style.position = 'fixed';
        proj.style.zIndex = '9998';
        proj.style.fontSize = '24px';
        proj.style.pointerEvents = 'none';

        const startX = fromRect.left + fromRect.width / 2;
        const startY = fromRect.top + fromRect.height / 2;
        const deltaX = (toRect.left + toRect.width / 2) - startX;
        const deltaY = (toRect.top + toRect.height / 2) - startY;

        proj.style.left = `${startX}px`;
        proj.style.top = `${startY}px`;
        document.body.appendChild(proj);

        proj.animate([
            { transform: 'translate(0,0)', opacity: 1 },
            { transform: `translate(${deltaX}px, ${deltaY}px)`, opacity: 0.1 }
        ], {
            duration,
            easing: 'linear',
            fill: 'forwards'
        }).onfinish = () => {
            proj.remove();
            if (typeof onHit === 'function') onHit();
        };
    }

    function ensureCircleStyle() {
        if (document.getElementById('tower-attack-circle-style')) return;
        const style = document.createElement('style');
        style.id = 'tower-attack-circle-style';
        style.textContent = `
            @keyframes towerAttackCircle {
                0% { transform: translate(-2px, 0); }
                25% { transform: translate(0, -2px); }
                50% { transform: translate(2px, 0); }
                75% { transform: translate(0, 2px); }
                100% { transform: translate(-2px, 0); }
            }
            .tower-attack-circle {
                animation: towerAttackCircle 0.4s linear infinite;
            }
        `;
        document.head.appendChild(style);
    }

    window.isAggressiveTowerInRange = isAggressiveTowerInRange;
    window.startAggressiveTowerAttack = startAggressiveTowerAttack;
})();
