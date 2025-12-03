// Movement and attack logic for Fighter troop.
// Moves like a chess king and attacks adjacent (orthogonal or diagonal) targets.
(function() {
    const ATTACK_DAMAGE = 65;
    const ATTACK_INTERVAL_MS = 1200;
    const MOVE_HEARTBEAT_MS = 1400;

    function isFighterAttackInRange(attacker, target) {
        if (!attacker || !target || !target.position) return false;
        const dr = Math.abs((attacker.position?.row ?? 0) - target.position.row);
        const dc = Math.abs((attacker.position?.col ?? 0) - target.position.col);
        return (dr <= 1 && dc <= 1 && (dr + dc > 0));
    }

    function startFighterAttack(attacker, target) {
        if (!attacker || (attacker.hp !== undefined && attacker.hp <= 0)) return;
        if (!target || (target.hp !== undefined && target.hp <= 0)) return;
        if (attacker.attack && attacker._attackInterval && attacker.currentTargetId === (target && target.id)) {
            return;
        }
        attacker.attack = true;
        attacker.currentTargetId = target?.id || null;

        if (attacker._attackInterval) clearInterval(attacker._attackInterval);

        const doSwing = () => {
            if (!attacker.attack || (attacker.hp !== undefined && attacker.hp <= 0)) return false;
            if (!target || (target.hp !== undefined && target.hp <= 0)) {
                attacker.attack = false;
                attacker.currentTargetId = null;
                return false;
            }
            if (!isFighterAttackInRange(attacker, target)) {
                attacker.attack = false;
                attacker.currentTargetId = null;
                return false;
            }

            const attackerEl = attacker.element || document.querySelector(`.board-cell[data-row="${attacker.position?.row}"][data-col="${attacker.position?.col}"]`);
            const targetEl = target.element || document.querySelector(`.board-cell[data-row="${target.position?.row}"][data-col="${target.position?.col}"]`);
            if (attackerEl && attackerEl.animate) {
                attackerEl.animate([
                    { transform: 'rotate(0deg)' },
                    { transform: 'rotate(360deg)' }
                ], {
                    duration: 400,
                    easing: 'ease-out',
                    fill: 'none'
                });
            }

            if (window.pieceDeployment) window.pieceDeployment.applyDamage(target, ATTACK_DAMAGE, attacker);
            return true;
        };

        // Hit immediately then continue at interval
        doSwing();
        attacker._attackInterval = setInterval(() => {
            if (!doSwing()) {
                clearInterval(attacker._attackInterval);
                attacker._attackInterval = null;
            }
        }, ATTACK_INTERVAL_MS);
    }

    function stopFighterAttack(attacker) {
        if (!attacker) return;
        attacker.attack = false;
        attacker.currentTargetId = null;
        if (attacker._attackInterval) {
            clearInterval(attacker._attackInterval);
            attacker._attackInterval = null;
        }
    }

    function handleFighterDeath(entry, moverInstance = null) {
        if (!entry) return;
        entry.attack = false;
        if (moverInstance && typeof moverInstance.stop === 'function') {
            moverInstance.stop();
        }
        const cell = document.querySelector(`.board-cell[data-row="${entry.position?.row}"][data-col="${entry.position?.col}"]`);
        const imgEl = entry.element ? entry.element.querySelector('img') : null;
        const imgSrc = imgEl ? imgEl.src : null;
        const host = cell || entry.element;

        if (entry.element) {
            entry.element.remove();
        }

        if (host && imgSrc) {
            const effect = document.createElement('div');
            effect.style.position = 'absolute';
            effect.style.left = '0';
            effect.style.top = '0';
            effect.style.width = '100%';
            effect.style.height = '100%';
            effect.style.pointerEvents = 'none';
            effect.style.overflow = 'hidden';
            effect.style.zIndex = '10';

            const leftHalf = document.createElement('div');
            const rightHalf = document.createElement('div');
            [leftHalf, rightHalf].forEach(half => {
                half.style.position = 'absolute';
                half.style.top = '0';
                half.style.width = '50%';
                half.style.height = '100%';
                half.style.backgroundImage = `url(${imgSrc})`;
                half.style.backgroundSize = '200% 100%';
                half.style.backgroundRepeat = 'no-repeat';
            });
            leftHalf.style.left = '0';
            leftHalf.style.backgroundPosition = 'left center';
            rightHalf.style.right = '0';
            rightHalf.style.backgroundPosition = 'right center';

            effect.appendChild(leftHalf);
            effect.appendChild(rightHalf);
            host.style.position = 'relative';
            host.appendChild(effect);

            leftHalf.animate([
                { transform: 'translate(0,0)', opacity: 1 },
                { transform: 'translate(-20px,0)', opacity: 0 }
            ], { duration: 800, easing: 'ease-out', fill: 'forwards' });
            rightHalf.animate([
                { transform: 'translate(0,0)', opacity: 1 },
                { transform: 'translate(20px,0)', opacity: 0 }
            ], { duration: 800, easing: 'ease-out', fill: 'forwards' }).onfinish = () => {
                effect.remove();
            };
        }
    }

    class FighterMover {
        constructor(state, boardState) {
            this.unit = state;
            this.board = boardState;
            this.moveTimer = null;
            this.unit._mover = this;
            this.unit.onBoard = true;
            setTimeout(() => this.startHeartbeat(), 800);
        }

        startHeartbeat() {
            if (this.moveTimer) return;
            this.moveTimer = setInterval(() => {
                if (!this.unit.onBoard) return;
                if (this.unit.attack) return;
                if (this.unit.hp !== undefined && this.unit.hp <= 0) return;
                this.stepTowardTarget();
            }, MOVE_HEARTBEAT_MS);
        }

        stop() {
            if (this.moveTimer) {
                clearInterval(this.moveTimer);
                this.moveTimer = null;
            }
        }

        findNearestTarget() {
            const pieces = this.board.pieces || [];
            const myType = this.unit.type;
            const myAllegiance = this.unit.allegiance || 'a';
            const candidates = pieces.filter(p => {
                if (p.id === this.unit.id) return false;
                if (p.hp !== undefined && p.hp <= 0) return false;
                if (!p.allegiance || p.allegiance === myAllegiance) return false;
                if (!window.isTargetable(myType, window.PieceRegistry[p.type]?.role)) return false;
                if (p.type === 'king_tower' && window.isKingTowerCellTargetable && !window.isKingTowerCellTargetable(p, pieces)) {
                    return false;
                }
                return true;
            });
            if (candidates.length === 0) return null;
            const { row: sr, col: sc } = this.unit.position;
            let best = null;
            let bestDist = Infinity;
            candidates.forEach(p => {
                const d = Math.abs(p.position.row - sr) + Math.abs(p.position.col - sc);
                if (d < bestDist) {
                    bestDist = d;
                    best = p;
                }
            });
            return best;
        }

        stepTowardTarget() {
            const target = this.findNearestTarget();
            if (!target) return;

            if (isFighterAttackInRange(this.unit, target)) {
                startFighterAttack(this.unit, target);
                return;
            }

            const { row: sr, col: sc } = this.unit.position;
            const { row: tr, col: tc } = target.position;

            // Evaluate all king moves (8 directions + orthogonal).
            const deltas = [
                { dr: -1, dc: -1 }, { dr: -1, dc: 0 }, { dr: -1, dc: 1 },
                { dr: 0, dc: -1 },                   { dr: 0, dc: 1 },
                { dr: 1, dc: -1 },  { dr: 1, dc: 0 }, { dr: 1, dc: 1 },
            ];

            const scored = deltas
                .map(({ dr, dc }) => ({ row: sr + dr, col: sc + dc }))
                .filter(pos => pos.row >= 0 && pos.row <= 7 && pos.col >= 0 && pos.col <= 7)
                .filter(pos => !(window.isCellBlocked && window.isCellBlocked(pos.row, pos.col)))
                .map(pos => {
                    const dist = Math.abs(pos.row - tr) + Math.abs(pos.col - tc);
                    return { pos, dist };
                })
                .sort((a, b) => {
                    if (a.dist !== b.dist) return a.dist - b.dist;
                    // Tie-break: if current column is a-d (0-3) prefer moving right; else prefer left.
                    const preferRight = sc <= 3;
                    if (preferRight) return b.pos.col - a.pos.col;
                    return a.pos.col - b.pos.col;
                });

            if (scored.length === 0) return;
            const next = scored[0].pos;

            if (typeof this.board.movePiece === 'function') {
                this.board.movePiece(this.unit.id, next);
            }
            this.unit.position = next;
        }
    }

    function createFighterMover(state, board) {
        const mover = new FighterMover(state, board);
        return mover;
    }

    window.isFighterAttackInRange = isFighterAttackInRange;
    window.startFighterAttack = startFighterAttack;
    window.stopFighterAttack = stopFighterAttack;
    window.createFighterMover = createFighterMover;
    window.handleFighterDeath = handleFighterDeath;
})();
