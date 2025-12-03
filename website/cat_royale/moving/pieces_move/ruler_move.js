// Ruler movement: user-controlled knight moves with elixir cost and cooldown.
// Click the ruler to highlight valid knight moves (lavender). Click a highlighted cell to move, costing 1 elixir and requiring 5s between moves.
(function() {
    const HIGHLIGHT_COLOR = 'rgba(200, 180, 255, 0.6)';
    const MOVE_COOLDOWN_MS = 5000;

    function findOccupant(row, col, board, allegianceFilter = null) {
        return (board?.pieces || []).find(p => {
            if (!p.position) return false;
            if (p.position.row !== row || p.position.col !== col) return false;
            if (allegianceFilter && p.allegiance !== allegianceFilter) return false;
            return (p.hp ?? p.maxHP ?? 1) > 0;
        });
    }

    class RulerMover {
        constructor(state, boardState) {
            this.unit = state;
            this.board = boardState;
            this.highlighted = new Set();
            this.lastMoveAt = 0;
            this.boardGrid = document.querySelector('.board-grid');
            this.cooldownTimer = null;
            this.onPieceClick = this.onPieceClick.bind(this);
            this.onBoardClick = this.onBoardClick.bind(this);
            this.bind();
        }

        bind() {
            if (this.unit?.element) {
                this.unit.element.style.cursor = 'pointer';
                this.unit.element.addEventListener('click', this.onPieceClick);
            }
            if (this.boardGrid) {
                this.boardGrid.addEventListener('click', this.onBoardClick);
            }
        }

        dispose() {
            if (this.unit?.element) {
                this.unit.element.removeEventListener('click', this.onPieceClick);
            }
            if (this.boardGrid) {
                this.boardGrid.removeEventListener('click', this.onBoardClick);
            }
            this.clearHighlights();
            this.setCooldownVisual(false);
            if (this.cooldownTimer) {
                clearTimeout(this.cooldownTimer);
                this.cooldownTimer = null;
            }
        }

        getKnightMoves() {
            const { row: sr, col: sc } = this.unit.position || {};
            if (sr === undefined || sc === undefined) return [];
            const deltas = [
                { dr: 2, dc: 1 }, { dr: 2, dc: -1 },
                { dr: -2, dc: 1 }, { dr: -2, dc: -1 },
                { dr: 1, dc: 2 }, { dr: 1, dc: -2 },
                { dr: -1, dc: 2 }, { dr: -1, dc: -2 },
            ];
            return deltas
                .map(({ dr, dc }) => ({ row: sr + dr, col: sc + dc }))
                .filter(pos => pos.row >= 0 && pos.row <= 7 && pos.col >= 0 && pos.col <= 7)
                .filter(pos => !(window.isCellBlocked && window.isCellBlocked(pos.row, pos.col)))
                .filter(pos => !findOccupant(pos.row, pos.col, this.board, this.unit.allegiance));
        }

        highlightMoves() {
            this.clearHighlights();
            const moves = this.getKnightMoves();
            console.log('Valid knight moves:', moves);
            moves.forEach(({ row, col }) => {
                const cell = document.querySelector(`.board-cell[data-row="${row}"][data-col="${col}"]`);
                if (!cell) {
                    console.warn(`Cell not found for row ${row}, col ${col}`);
                    return;
                }
                cell.dataset.originalBg = cell.dataset.originalBg || cell.style.backgroundColor || '';
                cell.style.backgroundColor = HIGHLIGHT_COLOR;
                this.highlighted.add(`${row},${col}`);
                console.log(`Highlighted cell at row ${row}, col ${col}`);
            });
            console.log('Total highlighted cells:', this.highlighted.size);
        }

        clearHighlights() {
            this.highlighted.forEach(key => {
                const [row, col] = key.split(',').map(Number);
                const cell = document.querySelector(`.board-cell[data-row="${row}"][data-col="${col}"]`);
                if (cell) {
                    cell.style.backgroundColor = cell.dataset.originalBg || '';
                    delete cell.dataset.originalBg;
                }
            });
            this.highlighted.clear();
        }

        canMove() {
            if (elixirManager?.currentElixir < 1) {
                console.log('Ruler cannot move: insufficient elixir', elixirManager?.currentElixir);
                return false;
            }
            if (Date.now() - this.lastMoveAt < MOVE_COOLDOWN_MS) {
                const remainingCooldown = MOVE_COOLDOWN_MS - (Date.now() - this.lastMoveAt);
                console.log('Ruler cannot move: cooldown remaining', remainingCooldown + 'ms');
                return false;
            }
            if (this.unit.hp !== undefined && this.unit.hp <= 0) {
                console.log('Ruler cannot move: dead', this.unit.hp);
                return false;
            }
            console.log('Ruler can move! Elixir:', elixirManager?.currentElixir, 'HP:', this.unit.hp);
            return true;
        }

        setCooldownVisual(active) {
            if (!this.unit?.element) return;
            this.unit.element.style.filter = active ? 'grayscale(1)' : '';
        }

        onPieceClick(e) {
            e.stopPropagation();
            console.log('Ruler clicked! Position:', this.unit.position);
            if (!this.canMove()) {
                this.setCooldownVisual(true);
                this.clearHighlights();
                return;
            }
            console.log('Highlighting moves...');
            this.highlightMoves();
        }

        onBoardClick(e) {
            if (this.highlighted.size === 0) return;
            const cell = e.target.closest?.('.board-cell');
            if (!cell) {
                this.clearHighlights();
                return;
            }
            const row = parseInt(cell.dataset.row, 10);
            const col = parseInt(cell.dataset.col, 10);
            const key = `${row},${col}`;
            if (!this.highlighted.has(key)) {
                this.clearHighlights();
                return;
            }
            if (!this.canMove()) {
                this.clearHighlights();
                return;
            }
            // Deduct elixir
            elixirManager.currentElixir -= 1;
            elixirManager.updateElixirDisplay();
            elixirManager.updateElixirBar();
            elixirManager.startElixirGeneration();

            if (typeof this.board.movePiece === 'function') {
                this.board.movePiece(this.unit.id, { row, col });
            }
            this.unit.position = { row, col };
            this.lastMoveAt = Date.now();
            if (typeof window.handleLocalRulerMove === 'function') {
                window.handleLocalRulerMove({
                    id: this.unit.id,
                    row,
                    col,
                    allegiance: this.unit.allegiance,
                });
            }
            this.setCooldownVisual(true);
            if (this.cooldownTimer) clearTimeout(this.cooldownTimer);
            this.cooldownTimer = setTimeout(() => {
                // Only clear if cooldown truly passed
                if (Date.now() - this.lastMoveAt >= MOVE_COOLDOWN_MS) {
                    this.setCooldownVisual(false);
                }
                this.cooldownTimer = null;
            }, MOVE_COOLDOWN_MS);
            this.clearHighlights();
        }
    }

    function createRulerMover(state, board) {
        return new RulerMover(state, board);
    }

    function handleRulerDeath(entry, moverInstance = null) {
        if (moverInstance && typeof moverInstance.dispose === 'function') {
            moverInstance.dispose();
        }
        const cell = entry?.position
            ? document.querySelector(`.board-cell[data-row="${entry.position.row}"][data-col="${entry.position.col}"]`)
            : null;
        if (cell) {
            const mark = document.createElement('div');
            mark.textContent = '🐒';
            mark.style.position = 'absolute';
            mark.style.left = '50%';
            mark.style.top = '50%';
            mark.style.transform = 'translate(-50%, -50%)';
            mark.style.fontSize = '36px';
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
        if (entry && entry.element) {
            entry.element.remove();
        }
    }

    window.createRulerMover = createRulerMover;
    window.handleRulerDeath = handleRulerDeath;
})();
