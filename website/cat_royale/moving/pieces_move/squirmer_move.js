// Movement logic for Squirmer troop (building-only attacker).
(function() {
    class SquirmerMover {
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
            }, 1400);
        }

        stop() {
            if (this.moveTimer) {
                clearInterval(this.moveTimer);
                this.moveTimer = null;
            }
        }

        findNearestTarget() {
            const pieces = this.board.pieces || [];
            const candidates = pieces.filter(p => {
                if (p.allegiance === this.unit.allegiance) return false;
                if (p.role !== 'building') return false;
                if (p.hp !== undefined && p.hp <= 0) return false;
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

            if (window.isSquirmerAttackInRange && window.isSquirmerAttackInRange(this.unit, target)) {
                if (window.startSquirmerAttack) {
                    window.startSquirmerAttack(this.unit, target);
                }
                return;
            }

            const sr = this.unit.position.row;
            const sc = this.unit.position.col;
            const tr = target.position.row;
            const tc = target.position.col;

            const rowStep = sr === tr ? 0 : (tr > sr ? 1 : -1);
            const leftStep = { row: sr, col: sc - 1 };
            const rightStep = { row: sr, col: sc + 1 };
            const forwardStep = { row: sr + rowStep, col: sc };

            const candidates = [];
            if (rowStep !== 0) candidates.push(forwardStep);
            candidates.push(leftStep, rightStep);

            const scored = candidates
                .filter(pos => pos.row >= 0 && pos.row <= 7 && pos.col >= 0 && pos.col <= 7)
                .filter(pos => !(window.isCellBlocked && window.isCellBlocked(pos.row, pos.col)))
                .map(pos => {
                    const dist = Math.abs(pos.row - tr) + Math.abs(pos.col - tc);
                    return { pos, dist };
                })
                .sort((a, b) => {
                    if (a.dist !== b.dist) return a.dist - b.dist;
                    const inLeftHalf = sc <= 3;
                    const aDelta = a.pos.col - sc;
                    const bDelta = b.pos.col - sc;
                    const aPref = inLeftHalf ? (aDelta > 0 ? -1 : aDelta < 0 ? 1 : 0) : (aDelta < 0 ? -1 : aDelta > 0 ? 1 : 0);
                    const bPref = inLeftHalf ? (bDelta > 0 ? -1 : bDelta < 0 ? 1 : 0) : (bDelta < 0 ? -1 : bDelta > 0 ? 1 : 0);
                    return aPref - bPref;
                });

            if (scored.length === 0) return;
            const next = scored[0].pos;

            if (typeof this.board.movePiece === 'function') {
                this.board.movePiece(this.unit.id, next);
            }
            this.unit.position = next;
        }
    }

    function createSquirmerMover(state, board) {
        const mover = new SquirmerMover(state, board);
        return mover;
    }

    window.createSquirmerMover = createSquirmerMover;
})();
