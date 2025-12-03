// Movement logic for Shouter troop.
// Exposed on window for non-module use.

class ShouterMover {
    constructor(shouterState, boardState) {
        // shouterState: { id, type, position: {row, col}, onBoard: false, isMoving: false }
        // boardState: {
        //   pieces: [{ id, type, position: {row, col} }],
        //   movePiece: (id, newPos) => void
        // }
        this.shouter = shouterState;
        this.board = boardState;
        this.moveTimer = null;
        this.highlightPath = typeof boardState.highlightPath === 'function' ? boardState.highlightPath : null;
        this.shouter._mover = this;
        this.shouter.shouter_move = false;
        // Heartbeat: ensure movement restarts when not attacking
        this.nudgeTimer = setInterval(() => {
            const onboard = this.shouter.onBoard || this.shouter.shouter_on_board;
            if (!onboard) return;
            if (this.shouter.attack) return;
            if (this.shouter.shouter_lived === false || (this.shouter.hp !== undefined && this.shouter.hp <= 0)) return;
            if (!this.shouter.isMoving) {
                this.startAutoMove();
            }
        }, 500);
    }

    // Call when shouter is deployed to the board.
    markDeployed() {
        this.shouter.onBoard = true;
        this.shouter.shouter_on_board = true;
        // Start moving after 2s.
        setTimeout(() => {
            this.startAutoMove();
        }, 2000);
    }

    startAutoMove() {
        const onboard = this.shouter.onBoard || this.shouter.shouter_on_board;
        if (!onboard || this.shouter.isMoving || this.shouter.attack || this.shouter.shouter_lived === false || (this.shouter.hp !== undefined && this.shouter.hp <= 0)) return;
        this.shouter.isMoving = true;
        this.shouter.shouter_move = true;
        // Move every 1s.
        this.moveTimer = setInterval(() => this.stepTowardTarget(), 1000);
    }

    stop() {
        if (this.moveTimer) {
            clearInterval(this.moveTimer);
            this.moveTimer = null;
        }
        this.shouter.isMoving = false;
        this.shouter.shouter_move = false;
    }

    stepTowardTarget() {
        if (this.shouter.attack) {
            this.stop();
            return;
        }
        if ((this.shouter.shouter_lived === false) || (this.shouter.hp !== undefined && this.shouter.hp <= 0)) {
            this.stop();
            return;
        }
        const target = this.findNearestTarget();
        if (!target) {
            if (this.highlightPath) this.highlightPath([]);
            return;
        }

        const { row: sr, col: sc } = this.shouter.position;
        const { row: tr, col: tc } = target.position;

        // If in attack range, stop moving and trigger attack behavior
        if (window.isInShouterAttackRange && window.isInShouterAttackRange(this.shouter, target)) {
            if (this.highlightPath) this.highlightPath([]);
            this.stop();
            if (window.startShouterAttack) {
                window.startShouterAttack(this.shouter, target);
            }
            return;
        }

        // Diagonal one-step toward nearest target; tie-break by board half (left half goes right, right half goes left)
        const rawDr = tr - sr;
        const rawDc = tc - sc;

        let dr = rawDr === 0 ? (sr <= 3 ? 1 : -1) : Math.sign(rawDr);
        let dc;
        if (rawDc === 0) {
            dc = sc <= 3 ? 1 : -1;
        } else {
            dc = Math.sign(rawDc);
            // If distance is symmetric, apply half-board preference
            if (Math.abs(rawDc) === Math.abs(rawDr)) {
                dc = sc <= 3 ? 1 : -1;
            }
        }

        // Keep within bounds
        if (sr + dr > 7 || sr + dr < 0) dr = -dr;
        if (sc + dc > 7 || sc + dc < 0) dc = -dc;

        const candidates = [];
        candidates.push({ row: sr + dr, col: sc + dc });
        // Fallback diagonal with opposite dc if blocked
        candidates.push({ row: sr + dr, col: sc - dc });

        let finalPos = null;
        for (const pos of candidates) {
            if (pos.row < 0 || pos.row > 7 || pos.col < 0 || pos.col > 7) continue;
            if (window.isCellBlocked && window.isCellBlocked(pos.row, pos.col)) continue;
            finalPos = pos;
            break;
        }

        if (!finalPos) {
            if (this.highlightPath) this.highlightPath([]);
            return;
        }

        // Update position via board API if provided
        if (typeof this.board.movePiece === 'function') {
            this.board.movePiece(this.shouter.id, finalPos);
        }
        this.shouter.position = finalPos;
    }

    buildPath(sr, sc, tr, tc) {
        const path = [];
        let r = sr;
        let c = sc;
        while (r !== tr || c !== tc) {
            r += Math.sign(tr - r);
            c += Math.sign(tc - c);
            path.push({ row: r, col: c });
        }
        return path;
    }

    findNearestTarget() {
        // Filter valid targets per registry
        const allPieces = this.board.pieces || [];
        const myType = this.shouter.type;
        const myAllegiance = this.shouter.allegiance || 'a';
        const candidates = allPieces.filter(p => {
            if (p.id === this.shouter.id) return false;
            if (p.hp !== undefined && p.hp <= 0) return false;
            if (p.type === 'shouter' && p.shouter_lived === false) return false;
            if (!p.allegiance || p.allegiance === myAllegiance) return false;
            if (!window.isTargetable(myType, window.PieceRegistry[p.type]?.role)) return false;
            if (p.type === 'king_tower' && window.isKingTowerCellTargetable && !window.isKingTowerCellTargetable(p, allPieces)) {
                return false;
            }
            return true;
        });
        if (candidates.length === 0) return null;

        const { row: sr, col: sc } = this.shouter.position;
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
}

// Convenience factory for simple usage without classes.
function createShouterMover(shouterState, boardState) {
    const mover = new ShouterMover(shouterState, boardState);
    mover.markDeployed();
    return mover;
}

window.ShouterMover = ShouterMover;
window.createShouterMover = createShouterMover;

function handleShouterDeath(entry, moverInstance = null) {
    if (!entry) return;
    entry.shouter_lived = false;
    entry.attack = false;
    if (moverInstance && typeof moverInstance.stop === 'function') {
        moverInstance.stop();
    }
    if (entry.element) entry.element.remove();
    const cell = document.querySelector(`.board-cell[data-row="${entry.position?.row}"][data-col="${entry.position?.col}"]`);
    if (cell) {
        const mark = document.createElement('div');
        mark.textContent = '?';
        mark.style.position = 'absolute';
        mark.style.left = '50%';
        mark.style.top = '50%';
        mark.style.transform = 'translate(-50%, -50%)';
        mark.style.fontSize = '32px';
        mark.style.fontWeight = 'bold';
        mark.style.color = '#555';
        mark.style.opacity = '1';
        mark.style.pointerEvents = 'none';
        cell.appendChild(mark);
        mark.animate([
            { opacity: 1 },
            { opacity: 0 }
        ], {
            duration: 3000,
            easing: 'ease-out',
            fill: 'forwards'
        }).onfinish = () => mark.remove();
    }
}

window.handleShouterDeath = handleShouterDeath;
