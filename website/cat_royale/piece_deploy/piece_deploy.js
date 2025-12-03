// Piece Deployment System (reconstructed with modularized HP/move/death helpers)
class PieceDeployment {
    constructor() {
        this.selectedCard = null;
        this.draggedCard = null;
        this.isDragging = false;
        this.draggedPiece = null;
        this.deployedPieces = [];
        this.boardPieces = [];
        this.activeMovers = {};
        this.activePaths = {};
        this.attackScanTimer = null;
        this.kingTowerShared = { a: null, b: null };
        this.playerSide = 'a';
    }

    setPlayerSide(side) {
        if (side === 'a' || side === 'b') {
            this.playerSide = side;
        } else {
            this.playerSide = 'spectate';
        }
    }

    isLocalPlayerActive() {
        return this.playerSide === 'a' || this.playerSide === 'b';
    }

    getMaxHPForType(type) {
        if (type === 'aggressive_tower') return window.AggressiveTowerHP?.maxHP || 600;
        if (type === 'solid_tower') return window.SolidTowerHP?.maxHP || 1000;
        if (type === 'king_tower') return window.KingTowerHP?.maxHP || 1800;
        if (type === 'shouter') return window.ShouterHP?.maxHP || 150;
        if (type === 'fighter') return window.FighterHP?.maxHP || 180;
        if (type === 'ruler') return window.RulerHP?.maxHP || 400;
        if (type === 'squirmer') return window.SquirmerHP?.maxHP || 400;
        return 100;
    }

    getDefaultCost(type) {
        if (type === 'shouter') return 3;
        if (type === 'squirmer') return 4;
        if (type === 'fighter') return 3;
        if (type === 'ruler') return 5;
        return 0;
    }

    getBoardImagePath(type, fallback = '') {
        const map = {
            shouter: '../pieces/shouter/shouter_board.png',
            fighter: '../pieces/fighter/fighter.png',
            ruler: '../pieces/ruler/ruler.png',
            squirmer: '../pieces/squirmer/squirmer_board.png',
            aggressive_tower: '../pieces/agressive_tower/aggressive_tower.png',
            solid_tower: '../pieces/solid_tower/solid_tower.png',
        };
        if (map[type]) return map[type];
        if (fallback) return fallback;
        return `../pieces/${type}/${type}.png`;
    }

    attachHealthBar(entry) {
        let anchor = entry.element;
        if (!anchor && entry.type === 'king_tower') {
            // King tower uses shared anchor injected in grid
            const anchors = [...document.querySelectorAll('.king-anchor')];
            anchor = anchors.find(el => el.dataset && el.dataset.allegiance === entry.allegiance) || anchors[0];
        }
        if (!anchor) {
            const cellAnchor = document.querySelector(`.board-cell[data-row="${entry.position?.row}"][data-col="${entry.position?.col}"]`);
            anchor = cellAnchor;
        }
        if (!anchor) return;

        // For king tower, reuse one bar per side
        if (entry.type === 'king_tower' && this.kingTowerShared[entry.allegiance]?.healthBar) {
            entry.healthBar = this.kingTowerShared[entry.allegiance].healthBar;
            return;
        }
        let factory = null;
        if (entry.type === 'aggressive_tower') factory = window.AggressiveTowerHP?.createHealthBar;
        else if (entry.type === 'solid_tower') factory = window.SolidTowerHP?.createHealthBar;
        else if (entry.type === 'king_tower') factory = window.KingTowerHP?.createHealthBar;
        else if (entry.type === 'shouter') factory = window.ShouterHP?.createHealthBar;
        else if (entry.type === 'fighter') factory = window.FighterHP?.createHealthBar;
        else if (entry.type === 'ruler') factory = window.RulerHP?.createHealthBar;
        else if (entry.type === 'squirmer') factory = window.SquirmerHP?.createHealthBar;
        if (typeof factory === 'function') {
            entry.healthBar = factory(anchor);
            if (entry.type === 'king_tower' && this.kingTowerShared[entry.allegiance]) {
                this.kingTowerShared[entry.allegiance].healthBar = entry.healthBar;
            }
            this.attachHealthTooltip(entry);
        }
    }

    attachHealthTooltip(entry) {
        if (!entry.healthBar || !entry.healthBar.barWrapper) return;
        const wrapper = entry.healthBar.barWrapper;
        let tooltip = null;

        const showTooltip = (e) => {
            if (!tooltip) {
                tooltip = document.createElement('div');
                tooltip.style.position = 'fixed';
                tooltip.style.padding = '4px 6px';
                tooltip.style.background = '#FFF';
                tooltip.style.color = '#000';
                tooltip.style.border = '1px solid #000';
                tooltip.style.borderRadius = '4px';
                tooltip.style.fontSize = '12px';
                tooltip.style.pointerEvents = 'none';
                document.body.appendChild(tooltip);
            }
            tooltip.textContent = `${entry.hp}/${entry.maxHP}`;
            tooltip.style.left = `${e.clientX + 8}px`;
            tooltip.style.top = `${e.clientY - 10}px`;
            tooltip.style.display = 'block';
        };

        const hideTooltip = () => {
            if (tooltip) tooltip.style.display = 'none';
        };

        wrapper.style.cursor = 'default';
        wrapper.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
        wrapper.addEventListener('mouseenter', showTooltip);
        wrapper.addEventListener('mousemove', showTooltip);
        wrapper.addEventListener('mouseleave', hideTooltip);
    }

    updateHealth(entry, newHP) {
        if (entry.type === 'king_tower') {
            this.updateKingHealth(entry.allegiance, newHP);
            return;
        }
        entry.hp = Math.max(0, Math.min(newHP, entry.maxHP));
        if (entry.healthBar && typeof entry.healthBar.update === 'function') {
            entry.healthBar.update(entry.hp);
        }
        if (entry.hp <= 0) {
            this.handleDeath(entry);
        }
    }

    updateKingHealth(allegiance, newHP) {
        const shared = this.kingTowerShared[allegiance];
        if (!shared) return;
        shared.hp = Math.max(0, Math.min(newHP, shared.maxHP));
        this.boardPieces
            .filter(p => p.type === 'king_tower' && p.allegiance === allegiance)
            .forEach(p => { p.hp = shared.hp; p.maxHP = shared.maxHP; });
        if (shared.healthBar && typeof shared.healthBar.update === 'function') {
            shared.healthBar.update(shared.hp);
        }
        if (shared.hp <= 0) {
            this.boardPieces
                .filter(p => p.type === 'king_tower' && p.allegiance === allegiance)
                .forEach(p => this.handleDeath(p));
        }
    }

    applyDamage(targetEntry, amount, attacker = null) {
        if (!targetEntry || typeof amount !== 'number') return;

        // Only HOST executes damage calculation
        if (window.IS_HOST !== true) {
            console.warn('[piece_deploy] CLIENT should not call applyDamage directly');
            return;
        }

        // Apply any active damage reduction (e.g., tower abilities)
        const reduction = targetEntry.damageReduction || 0;
        const effectiveAmount = Math.max(0, amount * (1 - reduction));
        targetEntry.be_attacked = true;
        targetEntry.attackedById = attacker?.id || null;
        targetEntry.attackedByType = attacker?.type || null;
        targetEntry.attackedByAllegiance = attacker?.allegiance || null;
        targetEntry.lastAttackedAt = Date.now();
        if (targetEntry._beAttackedTimer) {
            clearTimeout(targetEntry._beAttackedTimer);
        }
        targetEntry._beAttackedTimer = setTimeout(() => {
            targetEntry.be_attacked = false;
            targetEntry.attackedById = null;
            targetEntry.attackedByType = null;
            targetEntry.attackedByAllegiance = null;
            targetEntry._beAttackedTimer = null;
        }, 1200);

        // Calculate new HP
        let newHP;
        if (targetEntry.type === 'king_tower') {
            const shared = this.kingTowerShared[targetEntry.allegiance];
            const current = shared ? shared.hp : (targetEntry.hp ?? targetEntry.maxHP ?? 0);
            newHP = current - effectiveAmount;
            this.updateKingHealth(targetEntry.allegiance, newHP);
        } else {
            const current = targetEntry.hp ?? targetEntry.maxHP ?? 0;
            newHP = Math.max(0, Math.min(current - effectiveAmount, targetEntry.maxHP));
            targetEntry.hp = newHP;
            if (targetEntry.healthBar && typeof targetEntry.healthBar.update === 'function') {
                targetEntry.healthBar.update(targetEntry.hp);
            }
        }

        // Broadcast damage event
        if (typeof window.postToParent === 'function') {
            window.postToParent('state_update', {
                type: 'state_update',
                event: 'damage',
                piece_id: targetEntry.id,
                hp: newHP,
                attacker_id: attacker?.id,
                damage: effectiveAmount
            });
        }

        // Check for death
        if (newHP <= 0) {
            this.handleDeath(targetEntry);
        }
    }

    handleDeath(entry) {
        // Prevent duplicate death handling
        if (entry._isDead) return;
        entry._isDead = true;

        entry.attack = false;
        if (entry.type === 'shouter') {
            entry.shouter_lived = false;
        } else if (entry.type === 'aggressive_tower') {
            entry.aggressive_tower_lived = false;
        }
        if (entry.type === 'fighter') {
            entry.fighter_lived = false;
        } else if (entry.type === 'ruler') {
            entry.ruler_lived = false;
        }
        if (entry._beAttackedTimer) {
            clearTimeout(entry._beAttackedTimer);
            entry._beAttackedTimer = null;
        }

        // Call local death handlers
        if (entry.type === 'shouter') {
            if (typeof window.handleShouterDeath === 'function') {
                window.handleShouterDeath(entry, this.activeMovers[entry.id]);
            }
        } else if (entry.type === 'fighter') {
            if (typeof window.handleFighterDeath === 'function') {
                window.handleFighterDeath(entry, this.activeMovers[entry.id]);
            }
        } else if (entry.type === 'ruler') {
            if (typeof window.handleRulerDeath === 'function') {
                window.handleRulerDeath(entry, this.activeMovers[entry.id]);
            }
        } else if (entry.type === 'aggressive_tower') {
            if (typeof window.handleAggressiveTowerDeath === 'function') {
                window.handleAggressiveTowerDeath(entry);
            }
            this.stopTowerAttack(entry);
        } else if (entry.type === 'king_tower') {
            window.gameOver = true;
            console.log('Game over: King tower destroyed');
        }

        // Broadcast death event if HOST
        if (window.IS_HOST === true && typeof window.postToParent === 'function') {
            window.postToParent('state_update', {
                type: 'state_update',
                event: 'death',
                piece_id: entry.id,
                piece_type: entry.type,
                allegiance: entry.allegiance,
                position: entry.position
            });
        }
    }

    resetInvalidHighlights() {
        document.querySelectorAll('.board-cell').forEach(cell => {
            cell.classList.remove('invalid-flash');
            cell.classList.remove('path-highlight');
            cell.style.backgroundColor = '';
            if (cell.dataset.originalBg) delete cell.dataset.originalBg;
        });
        this.activePaths = {};
    }

    registerStaticPiece(type, row, col, allegiance = 'a', element = null) {
        const maxHP = this.getMaxHPForType(type);
        if (type === 'king_tower' && !this.kingTowerShared[allegiance]) {
            this.kingTowerShared[allegiance] = { hp: maxHP, maxHP, healthBar: null };
        }
        this.boardPieces.push({
            id: `static-${type}-${row}-${col}-${allegiance}`,
            type,
            role: (window.PieceRegistry && window.PieceRegistry[type]?.role) || 'building',
            position: { row, col },
            allegiance,
            element,
            maxHP,
            hp: type === 'king_tower' ? this.kingTowerShared[allegiance].hp : maxHP,
            be_attacked: false,
            attackedById: null,
            attackedByType: null,
            attackedByAllegiance: null,
            lastAttackedAt: null,
            _beAttackedTimer: null,
            shouter_lived: type === 'shouter' ? true : undefined,
            aggressive_tower_lived: type === 'aggressive_tower'
        });
        const entry = this.boardPieces[this.boardPieces.length - 1];
        this.attachHealthBar(entry);
    }

    movePiece(id, newPos) {
        const entry = this.boardPieces.find(p => p.id === id);
        if (!entry) return false;
        const cell = document.querySelector(`.board-cell[data-row="${newPos.row}"][data-col="${newPos.col}"]`);
        if (!cell) return false;

        entry.position = { ...newPos };

        if (entry.element) {
            const oldParent = entry.element.parentElement;
            if (oldParent) oldParent.removeChild(entry.element);
            cell.style.position = 'relative';
            cell.appendChild(entry.element);
            if (entry.healthBar && entry.healthBar.barWrapper && entry.healthBar.barWrapper.parentElement !== entry.element) {
                entry.element.appendChild(entry.healthBar.barWrapper);
            }
        }
        return true;
    }

    highlightPath(id, coords) {
        if (this.activePaths[id]) {
            this.activePaths[id].forEach(({ row, col }) => {
                const c = document.querySelector(`.board-cell[data-row="${row}"][data-col="${col}"]`);
                if (c) c.classList.remove('path-highlight');
            });
        }
        this.activePaths[id] = coords || [];
    }

    showInvalid(cell) {
        cell.classList.add('invalid-flash');
        setTimeout(() => {
            cell.classList.remove('invalid-flash');
            cell.style.backgroundColor = '';
        }, 300);
    }

    stopTowerAttack(tower) {
        if (!tower) return;
        tower.attack = false;
        if (tower._attackInterval) {
            clearInterval(tower._attackInterval);
            tower._attackInterval = null;
        }
        if (tower._firstAttackTimeout) {
            clearTimeout(tower._firstAttackTimeout);
            tower._firstAttackTimeout = null;
        }
        tower.currentTargetId = null;
        const anchor = tower.element || document.querySelector(`.board-cell[data-row="${tower.position?.row}"][data-col="${tower.position?.col}"]`);
        if (anchor) anchor.classList.remove('tower-attack-circle');
    }

    scanTowerAttacks() {
        const towers = this.boardPieces.filter(p => p.role === 'building' && (p.type === 'aggressive_tower' || p.type === 'solid_tower') && (p.hp ?? 1) > 0 && p.aggressive_tower_lived !== false);
        const troops = this.boardPieces.filter(p => p.role === 'troop' && (p.hp ?? 1) > 0 && p.shouter_lived !== false);

        towers.forEach(tower => {
            let best = null;
            let bestDist = Infinity;
            troops.forEach(t => {
                if (t.allegiance === tower.allegiance) return;
                if (!t.position) return;
                const dr = Math.abs((tower.position?.row ?? 0) - t.position.row);
                const dc = Math.abs((tower.position?.col ?? 0) - t.position.col);
                const d = Math.max(dr, dc);
                if (d < bestDist) {
                    bestDist = d;
                    best = t;
                }
            });

            const inRange = best && (
                (tower.type === 'aggressive_tower' && window.isAggressiveTowerInRange && window.isAggressiveTowerInRange(tower, best)) ||
                (tower.type === 'solid_tower' && window.isSolidTowerInRange && window.isSolidTowerInRange(tower, best))
            );

            if (inRange) {
                if (tower.type === 'aggressive_tower' && window.startAggressiveTowerAttack) {
                    window.startAggressiveTowerAttack(tower, best);
                } else if (tower.type === 'solid_tower' && window.startSolidTowerAttack) {
                    window.startSolidTowerAttack(tower, best);
                }
            } else {
                this.stopTowerAttack(tower);
            }
        });
    }

    isValidCell(row, col, pieceType = null, allegiance = 'a') {
        if (window.isCellBlocked && window.isCellBlocked(row, col)) return false;
        const isSideA = allegiance !== 'b';
        // Each side can only deploy on its own half
        if (isSideA && row >= 0 && row <= 3) return false;
        if (!isSideA && row >= 4 && row <= 7) return false;
        // Only shouter cannot be placed on home-row corners (a1/c1/f1/h1 or mirrored for side b)
        const shouterHomeRow = isSideA ? 7 : 0;
        if (pieceType === 'shouter' && row === shouterHomeRow && (col === 0 || col === 2 || col === 5 || col === 7)) {
            return false;
        }
        return true;
    }

    initializeCard(cardSlot, pieceType, imagePath, boardImagePath, cost) {
        cardSlot.dataset.pieceType = pieceType;
        cardSlot.dataset.imagePath = imagePath;
        cardSlot.dataset.boardImagePath = boardImagePath;
        cardSlot.dataset.cost = cost;
        cardSlot.innerHTML = '';

        const pieceImg = document.createElement('img');
        pieceImg.src = imagePath;
        pieceImg.style.width = '90%';
        pieceImg.style.height = '90%';
        pieceImg.style.objectFit = 'cover';
        pieceImg.style.borderRadius = '5px';
        pieceImg.style.pointerEvents = 'none';
        cardSlot.appendChild(pieceImg);

        this.setupCardEvents(cardSlot);
    }

    setupCardEvents(cardSlot) {
        cardSlot.addEventListener('mousedown', (e) => {
            if (!this.isLocalPlayerActive()) return;
            if (!cardSlot.dataset.pieceType) return;

            const cost = parseInt(cardSlot.dataset.cost);
            if (elixirManager.currentElixir < cost) {
                console.log(`Not enough elixir! Need ${cost}, have ${elixirManager.currentElixir}`);
                return;
            }

            this.draggedCard = cardSlot;
            this.isDragging = true;

            this.draggedPiece = document.createElement('div');
            this.draggedPiece.style.position = 'fixed';
            this.draggedPiece.style.width = '50px';
            this.draggedPiece.style.height = '50px';
            this.draggedPiece.style.pointerEvents = 'none';
            this.draggedPiece.style.zIndex = '9999';
            this.draggedPiece.style.opacity = '0.8';

            const img = document.createElement('img');
            img.src = cardSlot.dataset.boardImagePath;
            img.style.width = '100%';
            img.style.height = '100%';
            img.style.objectFit = 'contain';
            this.draggedPiece.appendChild(img);

            document.body.appendChild(this.draggedPiece);

            this.draggedPiece.style.left = (e.clientX - 25) + 'px';
            this.draggedPiece.style.top = (e.clientY - 25) + 'px';
        });

        cardSlot.addEventListener('click', (e) => {
            if (!this.isLocalPlayerActive()) return;
            if (!cardSlot.dataset.pieceType) return;
            if (this.isDragging) return;

            const cost = parseInt(cardSlot.dataset.cost);
            if (elixirManager.currentElixir < cost) {
                console.log(`Not enough elixir! Need ${cost}, have ${elixirManager.currentElixir}`);
                return;
            }

            if (this.selectedCard === cardSlot) {
                this.selectedCard.style.transform = '';
                this.selectedCard.style.boxShadow = '';
                this.selectedCard = null;
            } else {
                if (this.selectedCard) {
                    this.selectedCard.style.transform = '';
                    this.selectedCard.style.boxShadow = '';
                }
                this.selectedCard = cardSlot;
                this.selectedCard.style.transform = 'translateY(-10px)';
                this.selectedCard.style.boxShadow = '0 8px 20px rgba(139, 92, 246, 0.5)';
            }
        });
    }

    deployPiece(cell, cardSlot, options = {}) {
        const row = parseInt(cell.dataset.row);
        const col = parseInt(cell.dataset.col);

        const pieceType = options.pieceType || cardSlot?.dataset?.pieceType;
        if (!pieceType) {
            console.warn('No piece type provided for deployment');
            console.log('Invalid cell for deployment');
            return false;
        }

        const allegiance = options.allegiance || this.playerSide || 'a';
        const fromNetwork = options.fromNetwork || false;
        const isPlayerOwned = allegiance === this.playerSide;
        const rawCost = options.cost ?? parseInt(cardSlot?.dataset?.cost ?? this.getDefaultCost(pieceType));
        const cost = Number.isFinite(rawCost) ? rawCost : 0;

        console.log('[piece_deploy] deployPiece called', { row, col, pieceType, allegiance, fromNetwork, IS_HOST: window.IS_HOST });

        if (!this.isValidCell(row, col, pieceType, allegiance)) {
            console.log('Invalid cell for deployment');
            return false;
        }

        const shouldSpendElixir = !fromNetwork && isPlayerOwned && !options.skipElixir;
        if (shouldSpendElixir && elixirManager.currentElixir < cost) {
            console.log('Not enough elixir!');
            return false;
        }

        // HOST vs CLIENT branching: only one path should execute
        if (!fromNetwork) {
            if (window.IS_HOST === true) {
                // HOST mode: deploy locally and broadcast
                console.log('[piece_deploy] HOST mode: will deploy and broadcast');
            } else {
                // CLIENT mode: send request to host
                console.log('[piece_deploy] CLIENT mode: calling handleLocalDeployRequest');
                if (typeof window.handleLocalDeployRequest === 'function') {
                    window.handleLocalDeployRequest({
                        row,
                        col,
                        pieceType,
                        allegiance,
                        cost,
                        boardImagePath: options.boardImagePath || this.getBoardImagePath(pieceType, cardSlot?.dataset?.imagePath),
                    });
                } else {
                    console.error('[piece_deploy] handleLocalDeployRequest is not defined!');
                }
                return { requested: true };
            }
        }

        const piece = document.createElement('div');
        piece.className = 'deployed-piece';
        piece.dataset.pieceType = pieceType;
        piece.style.position = 'absolute';
        piece.style.width = '100%';
        piece.style.height = '100%';
        piece.style.zIndex = '5';
        // Allow clicks for user-controlled movers (e.g., ruler) on local side only.
        piece.style.pointerEvents = pieceType === 'ruler' && isPlayerOwned ? 'auto' : 'none';
        piece.style.backgroundColor = '#FFFFFF';
        piece.style.border = '4px solid #5C4033';
        piece.style.boxSizing = 'border-box';
        piece.style.borderRadius = '5px';
        piece.style.display = 'flex';
        piece.style.alignItems = 'center';
        piece.style.justifyContent = 'center';

        const img = document.createElement('img');
        // Use board image; ensure squirmer uses its board variant
        const boardImg = options.boardImagePath
            || (pieceType === 'squirmer'
                ? (cardSlot?.dataset?.boardImagePath || '../pieces/squirmer/squirmer_board.png')
                : (cardSlot?.dataset?.boardImagePath || this.getBoardImagePath(pieceType, cardSlot?.dataset?.imagePath)));
        img.src = boardImg;
        img.style.width = '90%';
        img.style.height = '90%';
        img.style.objectFit = 'contain';
        piece.appendChild(img);

        cell.style.position = 'relative';
        cell.appendChild(piece);

        const pieceId = options.id || `piece-${Date.now()}-${Math.random().toString(16).slice(2)}`;
        const role = (window.PieceRegistry && window.PieceRegistry[pieceType]?.role) || 'troop';
        const maxHP = this.getMaxHPForType(pieceType);
        const pieceEntry = {
            id: pieceId,
            type: pieceType,
            role,
            position: { row, col },
            element: piece,
            allegiance,
            maxHP,
            hp: maxHP,
            boardImagePath: boardImg,
            shouter_on_board: pieceType === 'shouter',
            be_attacked: false,
            attackedById: null,
            attackedByType: null,
            attackedByAllegiance: null,
            lastAttackedAt: null,
            _beAttackedTimer: null,
            shouter_lived: pieceType === 'shouter' ? true : undefined,
            aggressive_tower_lived: pieceType === 'aggressive_tower'
        };
        this.boardPieces.push(pieceEntry);
        this.attachHealthBar(pieceEntry);

        if (shouldSpendElixir) {
            elixirManager.currentElixir -= cost;
            elixirManager.updateElixirDisplay();
            elixirManager.updateElixirBar();
            elixirManager.startElixirGeneration();
        }

        if (pieceType === 'shouter' && window.createShouterMover) {
            const mover = window.createShouterMover(pieceEntry, {
                pieces: this.boardPieces,
                movePiece: this.movePiece.bind(this),
                highlightPath: (coords) => this.highlightPath(pieceId, coords)
            });
            this.activeMovers[pieceEntry.id] = mover;
            pieceEntry._mover = mover;
        } else if (pieceType === 'squirmer' && window.createSquirmerMover) {
            const mover = window.createSquirmerMover(pieceEntry, {
                pieces: this.boardPieces,
                movePiece: this.movePiece.bind(this)
            });
            this.activeMovers[pieceEntry.id] = mover;
            pieceEntry._mover = mover;
        } else if (pieceType === 'fighter' && window.createFighterMover) {
            const mover = window.createFighterMover(pieceEntry, {
                pieces: this.boardPieces,
                movePiece: this.movePiece.bind(this)
            });
            this.activeMovers[pieceEntry.id] = mover;
            pieceEntry._mover = mover;
        } else if (pieceType === 'ruler' && window.createRulerMover) {
            const mover = window.createRulerMover(pieceEntry, {
                pieces: this.boardPieces,
                movePiece: this.movePiece.bind(this)
            });
            this.activeMovers[pieceEntry.id] = mover;
            pieceEntry._mover = mover;
        }

        // Only call handleLocalDeploy if HOST mode
        if (!fromNetwork && window.IS_HOST === true) {
            if (typeof window.handleLocalDeploy === 'function') {
                console.log('[piece_deploy] HOST mode: calling handleLocalDeploy');
                window.handleLocalDeploy({
                    id: pieceId,
                    row,
                    col,
                    pieceType,
                    allegiance,
                    cost,
                    boardImagePath: boardImg,
                });
            } else {
                console.error('[piece_deploy] handleLocalDeploy is not defined!');
            }
        }

        this.deployedPieces.push({
            row: row,
            col: col,
            type: pieceType,
            allegiance,
            element: piece
        });

        console.log(`Deployed ${pieceType} (${allegiance}) at row ${row}, col ${col}`);
        return pieceEntry;
    }

    initialize() {
        document.addEventListener('mousemove', (e) => {
            if (this.isDragging && this.draggedPiece) {
                this.draggedPiece.style.left = (e.clientX - 25) + 'px';
                this.draggedPiece.style.top = (e.clientY - 25) + 'px';
            }
        });

        document.addEventListener('mouseup', (e) => {
            if (!this.isDragging) return;

            this.isDragging = false;

            if (this.draggedPiece) {
                this.draggedPiece.remove();
                this.draggedPiece = null;
            }

            const target = document.elementFromPoint(e.clientX, e.clientY);
            if (target && target.classList.contains('board-cell')) {
                const row = parseInt(target.dataset.row);
                const col = parseInt(target.dataset.col);

                if (this.isValidCell(row, col, this.draggedCard?.dataset?.pieceType, this.playerSide)) {
                    this.deployPiece(target, this.draggedCard);
                } else {
                    this.showInvalid(target);
                }
            }

            this.draggedCard = null;
            this.resetInvalidHighlights();
        });

        const cells = document.querySelectorAll('.board-cell');
        cells.forEach(cell => {
            cell.addEventListener('click', (e) => {
                if (!this.selectedCard) return;

                const row = parseInt(cell.dataset.row);
                const col = parseInt(cell.dataset.col);

                if (this.isValidCell(row, col, this.selectedCard?.dataset?.pieceType, this.playerSide)) {
                    const success = this.deployPiece(cell, this.selectedCard);
                    if (success) {
                        this.selectedCard.style.transform = '';
                        this.selectedCard.style.boxShadow = '';
                        this.selectedCard = null;
                    }
                } else {
                    this.showInvalid(cell);
                }
            });

            cell.addEventListener('mouseenter', (e) => {
                if (!this.selectedCard && !this.isDragging) return;

                const row = parseInt(cell.dataset.row);
                const col = parseInt(cell.dataset.col);

                const currentType = (this.selectedCard || this.draggedCard)?.dataset?.pieceType || null;
                if (!this.isValidCell(row, col, currentType, this.playerSide)) {
                    cell.dataset.originalBg = cell.style.backgroundColor;
                    cell.classList.add('invalid-flash');
                }
            });

            cell.addEventListener('mouseleave', (e) => {
                if (!this.selectedCard && !this.isDragging) return;

                const row = parseInt(cell.dataset.row);
                const col = parseInt(cell.dataset.col);

                const currentType = (this.selectedCard || this.draggedCard)?.dataset?.pieceType || null;
                if (!this.isValidCell(row, col, currentType, this.playerSide)) {
                    cell.classList.remove('invalid-flash');
                    cell.style.backgroundColor = cell.dataset.originalBg || '';
                    delete cell.dataset.originalBg;
                }
            });
        });

        console.log('Piece deployment system initialized');

        if (!this.attackScanTimer) {
            this.attackScanTimer = setInterval(() => this.scanTowerAttacks(), 250);
        }
    }
}

const pieceDeployment = new PieceDeployment();
window.pieceDeployment = pieceDeployment;
