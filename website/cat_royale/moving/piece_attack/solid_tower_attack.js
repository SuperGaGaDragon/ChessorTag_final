// Solid tower attack: engages troops within 2 tiles (Chebyshev distance).
// When attacking, it bobs vertically and fires a 📱 projectile toward the target every 1s.

(function() {
    const INTERVAL_MS = 1000;
    const SPEED_MS = 900;
    const DAMAGE = 40;

    ensureBobStyle();

    function isInQuarter(attacker, target) {
        if (!attacker?.position || !target?.position) return false;
        const myRowTop = attacker.position.row <= 3;
        const myColLeft = attacker.position.col <= 3;
        const rowOk = myRowTop ? target.position.row <= 3 : target.position.row >= 4;
        const colOk = myColLeft ? target.position.col <= 3 : target.position.col >= 4;
        return rowOk && colOk;
    }

    function isSolidTowerInRange(attacker, target) {
        if (!attacker || !target || target.role !== 'troop') return false;
        return isInQuarter(attacker, target);
    }

    function startSolidTowerAttack(attacker, target) {
        // Only HOST executes attack logic
        if (window.IS_HOST !== true) {
            console.log('[solid_tower_attack] CLIENT mode: skip attack execution');
            return;
        }

        if (!attacker || (attacker.hp !== undefined && attacker.hp <= 0)) return;
        if (attacker.attack && attacker._attackInterval && attacker.currentTargetId === (target && target.id)) {
            return;
        }
        attacker.attack = true;
        attacker.currentTargetId = target?.id || null;
        const attackerEl = getAnchorElement(attacker);
        applyBobMotion(attackerEl);

        if (attacker._attackInterval) clearInterval(attacker._attackInterval);

        const fire = () => {
            if (!attacker.attack || (attacker.hp !== undefined && attacker.hp <= 0)) return false;
            if (!target || target.role !== 'troop' || (target.hp !== undefined && target.hp <= 0)) {
                attacker.attack = false;
                attacker.currentTargetId = null;
                return false;
            }
            if (!isSolidTowerInRange(attacker, target)) {
                attacker.attack = false;
                attacker.currentTargetId = null;
                return false;
            }
            const targetEl = getAnchorElement(target);
            const anchor = attackerEl || getAnchorElement(attacker);
            if (!anchor || !targetEl) return false;
            spawnProjectile(anchor, targetEl, '📱', SPEED_MS, () => {
                if (window.pieceDeployment) window.pieceDeployment.applyDamage(target, DAMAGE, attacker);
            });
            return true;
        };

        fire();

        attacker._attackInterval = setInterval(() => {
            if (!fire()) {
                clearInterval(attacker._attackInterval);
                attacker._attackInterval = null;
            }
        }, INTERVAL_MS);
    }

    function applyBobMotion(el) {
        if (!el) return;
        el.classList.add('tower-attack-bob');
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

    function ensureBobStyle() {
        if (document.getElementById('tower-attack-bob-style')) return;
        const style = document.createElement('style');
        style.id = 'tower-attack-bob-style';
        style.textContent = `
            @keyframes towerAttackBob {
                0% { transform: translateY(-2px); }
                50% { transform: translateY(2px); }
                100% { transform: translateY(-2px); }
            }
            .tower-attack-bob {
                animation: towerAttackBob 0.35s linear infinite;
            }
        `;
        document.head.appendChild(style);
    }

    window.isSolidTowerInRange = isSolidTowerInRange;
    window.startSolidTowerAttack = startSolidTowerAttack;
})();
