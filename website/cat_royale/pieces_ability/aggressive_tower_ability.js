// Ability logic for switching player towers between solid/aggressive.
// Exposes helpers on window.AggressiveTowerAbility for use in game_page.html.
(function() {
    const ABILITY2_COST = 2;

    const ability2CooldownUntil = { a: 0, b: 0 };

    function ensureAbilityState() {
        if (!window.TowerAbilityState) {
            window.TowerAbilityState = {
                a: { solidActive: false, aggressiveActive: false },
                b: { solidActive: false, aggressiveActive: false }
            };
        }
        return window.TowerAbilityState;
    }

    function setAbilityLock(key, active, side = 'a') {
        const state = ensureAbilityState();
        const normalizedSide = side === 'b' ? 'b' : 'a';
        if (!state[normalizedSide]) {
            state[normalizedSide] = { solidActive: false, aggressiveActive: false };
        }
        state[normalizedSide][key] = !!active;
    }

    function isAnyAbilityActive(side = 'a') {
        const state = window.TowerAbilityState;
        const normalizedSide = side === 'b' ? 'b' : 'a';
        if (!state || !state[normalizedSide]) return false;
        return !!(state[normalizedSide].solidActive || state[normalizedSide].aggressiveActive);
    }

    function getCooldownUntil(allegiance) {
        const side = allegiance === 'b' ? 'b' : 'a';
        return ability2CooldownUntil[side] || 0;
    }

    function setCooldownUntil(allegiance, ts) {
        const side = allegiance === 'b' ? 'b' : 'a';
        ability2CooldownUntil[side] = ts;
    }

    function getMaxHpForTower(type) {
        if (type === 'solid' || type === 'solid_tower') return window.SolidTowerHP?.maxHP || 1000;
        if (type === 'aggressive' || type === 'aggressive_tower') return window.AggressiveTowerHP?.maxHP || 600;
        return 1000;
    }

    function getTowersByAllegiance(allegiance) {
        if (!window.pieceDeployment) return [];
        return (pieceDeployment.boardPieces || []).filter(p =>
            p.allegiance === allegiance &&
            (p.type === 'solid_tower' || p.type === 'aggressive_tower')
        );
    }

    function canSwitchTowers(allegiance) {
        if (typeof elixirManager === 'undefined') return false;
        if (!elixirManager.hasEnough(1, allegiance)) return false;
        const side = allegiance === 'b' ? 'b' : 'a';
        if (isAnyAbilityActive(side)) return false;
        const towers = getTowersByAllegiance(allegiance);
        if (towers.length === 0) return false;
        return towers.every(t => !t.be_attacked);
    }

    function updateToggleDisabled(toggleEl, allegiance = 'a') {
        if (!toggleEl) return;
        const canToggle = canSwitchTowers(allegiance);
        if (canToggle) {
            toggleEl.classList.remove('disabled');
        } else {
            toggleEl.classList.add('disabled');
        }
    }

    function refreshHealthBar(tower) {
        if (!tower) return;
        const anchor = tower.element || document.querySelector(`.board-cell[data-row="${tower.position?.row}"][data-col="${tower.position?.col}"]`);
        if (!anchor) return;

        // Remove old health bar
        if (tower.healthBar && tower.healthBar.barWrapper && tower.healthBar.barWrapper.parentElement) {
            tower.healthBar.barWrapper.remove();
        }

        // Get the correct factory based on tower type
        let factory = null;
        if (tower.type === 'aggressive_tower') factory = window.AggressiveTowerHP?.createHealthBar;
        if (tower.type === 'solid_tower') factory = window.SolidTowerHP?.createHealthBar;

        if (typeof factory === 'function') {
            // Create new health bar with correct maxHP
            tower.healthBar = factory(anchor);

            // Update to current HP value
            if (tower.healthBar && typeof tower.healthBar.update === 'function') {
                tower.healthBar.update(tower.hp);
            }

            // Reattach tooltip if available
            if (window.pieceDeployment && typeof window.pieceDeployment.attachHealthTooltip === 'function') {
                window.pieceDeployment.attachHealthTooltip(tower);
            }
        }
    }

    function rescaleTowerStats(towers, newType) {
        const registryType = newType === 'solid' ? 'solid_tower' : 'aggressive_tower';
        const spriteFor = (allegiance = 'a') => {
            if (allegiance === 'a') {
                return registryType === 'solid_tower'
                    ? '../pieces/solid_tower/solid_tower_a.png'
                    : '../pieces/agressive_tower/aggressive_tower_a.png';
            }
            return registryType === 'solid_tower'
                ? '../pieces/solid_tower/solid_tower.png'
                : '../pieces/agressive_tower/aggressive_tower.png';
        };
        towers.forEach(tower => {
            const prevMax = tower.maxHP || getMaxHpForTower(tower.type);
            const prevHp = tower.hp ?? prevMax;
            const ratio = prevMax ? Math.max(0, Math.min(prevHp / prevMax, 1)) : 1;
            const nextMax = getMaxHpForTower(registryType);
            tower.type = registryType;
            tower.maxHP = nextMax;
            tower.hp = Math.round(nextMax * ratio);
            tower.boardImagePath = spriteFor(tower.allegiance || 'a');
            refreshHealthBar(tower);
            const img = tower.element ? tower.element.querySelector('img') : null;
            if (img) img.src = tower.boardImagePath;
        });
    }

    function applyToggleVisual(toggleEl, playerTowerType, playerAllegiance = 'a') {
        if (!toggleEl) return;
        const img1 = toggleEl.querySelector('.tower-img-1');
        const img2 = toggleEl.querySelector('.tower-img-2');
        if (!img1 || !img2) return;

        // Update image sources based on allegiance
        const towerSpriteFor = window.towerSpriteFor || ((type, allegiance) => {
            if (allegiance === 'a') {
                if (type === 'solid' || type === 'solid_tower') return '../pieces/solid_tower/solid_tower_a.png';
                if (type === 'aggressive' || type === 'aggressive_tower') return '../pieces/agressive_tower/aggressive_tower_a.png';
            }
            if (type === 'solid' || type === 'solid_tower') return '../pieces/solid_tower/solid_tower.png';
            if (type === 'aggressive' || type === 'aggressive_tower') return '../pieces/agressive_tower/aggressive_tower.png';
            return '';
        });

        img1.src = towerSpriteFor('solid', playerAllegiance);
        img2.src = towerSpriteFor('aggressive', playerAllegiance);

        const oppositeType = playerTowerType === 'solid' ? 'aggressive' : 'solid';
        if (oppositeType === 'solid') {
            img1.style.display = 'block';
            img2.style.display = 'none';
        } else {
            img1.style.display = 'none';
            img2.style.display = 'block';
        }
    }

    function switchPlayerTowers(state) {
        if (window.IS_HOST !== true) return state?.getPlayerTowerType?.();
        const currentPlayerTowers = (state?.getCurrentPlayerTowers?.() || []).filter(Boolean);
        if (currentPlayerTowers.length === 0) return state?.getPlayerTowerType?.();

        // Get player allegiance from pieceDeployment
        const playerAllegiance = window.pieceDeployment?.playerSide || window.MY_SIDE || 'a';

        if (!canSwitchTowers(playerAllegiance)) {
            console.log('Cannot switch towers: either under attack or not enough elixir.');
            return state?.getPlayerTowerType?.();
        }

        const currentType = currentPlayerTowers[0].dataset.towerType;
        const newType = currentType === 'solid' ? 'aggressive' : 'solid';

        // Use correct allegiance-specific image path
        const towerSpriteFor = window.towerSpriteFor || ((type, allegiance) => {
            if (allegiance === 'a') {
                if (type === 'solid' || type === 'solid_tower') return '../pieces/solid_tower/solid_tower_a.png';
                if (type === 'aggressive' || type === 'aggressive_tower') return '../pieces/agressive_tower/aggressive_tower_a.png';
            }
            if (type === 'solid' || type === 'solid_tower') return '../pieces/solid_tower/solid_tower.png';
            if (type === 'aggressive' || type === 'aggressive_tower') return '../pieces/agressive_tower/aggressive_tower.png';
            return '';
        });

        const newImagePath = towerSpriteFor(newType, playerAllegiance);

        if (!elixirManager.spend(1, playerAllegiance)) {
            console.log('Cannot switch towers: insufficient elixir for host');
            return state?.getPlayerTowerType?.();
        }

        currentPlayerTowers.forEach(tower => {
            const img = tower.querySelector('img');
            if (img) img.src = newImagePath;
            // Update dataset to match new tower type
            tower.dataset.towerType = newType;
        });

        const playerTowers = getTowersByAllegiance(playerAllegiance);
        rescaleTowerStats(playerTowers, newType);

        console.log(`[AggressiveTowerAbility] Switched ${playerAllegiance} towers to ${newType}. Elixir: ${elixirManager.currentElixir}`);
        state?.setPlayerTowerType?.(newType);
        applyToggleVisual(state?.toggleElement, newType, playerAllegiance);
        if (typeof window.postToParent === 'function') {
            const serialized = playerTowers.map(t => {
                // Use correct sprite based on hp state
                let imagePath = t.boardImagePath;
                const currentHp = t.hp ?? t.maxHP ?? 1;
                if (currentHp <= 0) {
                    // Dead state - use cooked image
                    if (t.type === 'aggressive_tower') {
                        imagePath = '../pieces/agressive_tower/cooked_aggressive_tower.png';
                    } else if (t.type === 'solid_tower') {
                        imagePath = '../pieces/solid_tower/cooked_solid_tower.png';
                    }
                }
                return {
                    id: t.id,
                    row: t.position?.row,
                    col: t.position?.col,
                    type: t.type,
                    hp: t.hp,
                    max_hp: t.maxHP,
                    allegiance: t.allegiance,
                    board_image_path: imagePath
                };
            });
            window.postToParent('state_update', {
                type: 'state_update',
                event: 'tower_switch',
                side: playerAllegiance,
                tower_type: newType,
                towers: serialized
            });
        }
        return newType;
    }

    function broadcastAggressiveAbility(side, payload) {
        if (typeof window.postToParent !== 'function') return;
        window.postToParent('state_update', {
            type: 'state_update',
            event: 'tower_ability_aggressive',
            side,
            ...payload
        });
    }

    function runAggressiveAbility2(playerAllegiance, getPlayerTowerType) {
        if (Date.now() < getCooldownUntil(playerAllegiance)) return false;
        if (getPlayerTowerType() !== 'aggressive') return false;
        const towers = getTowersByAllegiance(playerAllegiance).filter(t => t.type === 'aggressive_tower' && !t.attack);
        if (towers.length === 0) return false;

        if (!elixirManager.hasEnough(ABILITY2_COST, playerAllegiance)) {
            console.log('Not enough elixir for aggressive ability.');
            if (typeof window.postToParent === 'function') {
                window.postToParent('state_update', {
                    type: 'state_update',
                    event: 'error',
                    code: 'elixir_insufficient',
                    side: playerAllegiance,
                    action: 'tower_ability_aggressive',
                    cost: ABILITY2_COST
                });
            }
            return false;
        }
        if (!elixirManager.spend(ABILITY2_COST, playerAllegiance)) {
            console.log('Spend failed for aggressive ability.');
            return false;
        }

        setAbilityLock('aggressiveActive', true, playerAllegiance);

        const forwardSlots = playerAllegiance === 'a'
            ? [
                { fromRow: 6, fromCol: 1, toRow: 5, toCol: 1 }, // b2 -> b3
                { fromRow: 6, fromCol: 6, toRow: 5, toCol: 6 }  // g2 -> g3
              ]
            : [
                { fromRow: 1, fromCol: 1, toRow: 2, toCol: 1 }, // b7 -> b6
                { fromRow: 1, fromCol: 6, toRow: 2, toCol: 6 }  // g7 -> g6
              ];

        const applied = [];

        towers.forEach(t => {
            // Apply 25% damage reduction
            t.damageReduction = 0.25;
            // Swap image to ability form
            const img = t.element ? t.element.querySelector('img') : null;
            const previousImg = img ? img.src : t.boardImagePath;
            if (img) {
                t._aggOriginalImgSrc = previousImg || t._aggOriginalImgSrc;
                img.src = '../pieces/agressive_tower/aggressive_tower_ability_2.png';
            }
            t.boardImagePath = '../pieces/agressive_tower/aggressive_tower_ability_2.png';

            const slot = forwardSlots.find(s => s.fromRow === t.position?.row && s.fromCol === t.position?.col);
            if (slot && window.pieceDeployment && typeof window.pieceDeployment.movePiece === 'function') {
                t._originalPosition = { ...t.position };
                window.pieceDeployment.movePiece(t.id, { row: slot.toRow, col: slot.toCol });
                t.position = { row: slot.toRow, col: slot.toCol };
            }

            applied.push({
                id: t.id,
                row: t.position?.row,
                col: t.position?.col,
                original_row: t._originalPosition?.row,
                original_col: t._originalPosition?.col,
                original_image: t._aggOriginalImgSrc || previousImg,
                board_image_path: t.boardImagePath,
                damage_reduction: t.damageReduction
            });
        });

        console.log(`[AggressiveTowerAbility] Activated ability for ${playerAllegiance} towers`);

        if (typeof window.postToParent === 'function') {
            broadcastAggressiveAbility(playerAllegiance, {
                targets: applied,
                duration_ms: 3000
            });
        }

        setTimeout(() => {
            towers.forEach(t => {
                t.damageReduction = 0;
                // revert image - use allegiance-specific sprite via towerSpriteFor
                const img = t.element ? t.element.querySelector('img') : null;
                const towerSpriteFor = window.towerSpriteFor || ((type, allegiance) => {
                    if (allegiance === 'a') {
                        if (type === 'solid' || type === 'solid_tower') return '../pieces/solid_tower/solid_tower_a.png';
                        if (type === 'aggressive' || type === 'aggressive_tower') return '../pieces/agressive_tower/aggressive_tower_a.png';
                    }
                    if (type === 'solid' || type === 'solid_tower') return '../pieces/solid_tower/solid_tower.png';
                    if (type === 'aggressive' || type === 'aggressive_tower') return '../pieces/agressive_tower/aggressive_tower.png';
                    return '';
                });
                const defaultSprite = towerSpriteFor('aggressive', t.allegiance || 'a');
                const fallback = t._aggOriginalImgSrc || defaultSprite;
                if (img) {
                    img.src = fallback;
                }
                t.boardImagePath = fallback;
                if (t._originalPosition && window.pieceDeployment && typeof window.pieceDeployment.movePiece === 'function') {
                    window.pieceDeployment.movePiece(t.id, { ...t._originalPosition });
                    t.position = { ...t._originalPosition };
                }
            });
            setCooldownUntil(playerAllegiance, Date.now() + 5000);
            setAbilityLock('aggressiveActive', false, playerAllegiance);
        }, 3000);

        return true;
    }

    function handleAggressiveAbilityRequest(side, getPlayerTowerType) {
        const playerAllegiance = side || window.pieceDeployment?.playerSide || window.MY_SIDE || 'a';
        if (window.IS_HOST !== true) {
            if (typeof window.postToParent === 'function') {
                window.postToParent('state_update', {
                    type: 'state_update',
                    event: 'tower_ability_aggressive_request',
                    side: playerAllegiance
                });
            }
            return;
        }
        runAggressiveAbility2(playerAllegiance, getPlayerTowerType);
    }

    function init(options = {}) {
        const toggleElement = options.toggleElement;
        if (!toggleElement) return;
        const isAuthority = window.IS_HOST === true;

        const getCurrentPlayerTowers = options.getCurrentPlayerTowers || (() => []);
        const getPlayerTowerType = options.getPlayerTowerType || (() => null);
        const setPlayerTowerType = options.setPlayerTowerType || (() => {});
        let ability2Armed = false;
        let ability2ArmTimeout = null;
        let ability2Timer = null;

        toggleElement.addEventListener('click', (e) => {
            e.stopPropagation();
            ability2Armed = false;
            if (ability2ArmTimeout) {
                clearTimeout(ability2ArmTimeout);
                ability2ArmTimeout = null;
            }
            const playerAllegiance = window.pieceDeployment?.playerSide || window.MY_SIDE || 'a';
            if (!isAuthority) {
                if (typeof window.postToParent === 'function') {
                    window.postToParent('state_update', {
                        type: 'state_update',
                        event: 'tower_switch_request',
                        side: playerAllegiance
                    });
                }
                return;
            }
            switchPlayerTowers({
                toggleElement,
                getCurrentPlayerTowers,
                getPlayerTowerType,
                setPlayerTowerType
            });
            // Immediately refresh clickable state in case elixir/attack status changed
            updateToggleDisabled(toggleElement, playerAllegiance);
        });

        function armAbilityFromCell(cell) {
            if (!cell) return;
            const row = parseInt(cell.dataset.row, 10);
            const col = parseInt(cell.dataset.col, 10);
            const allowed = (
                (row === 6 && col === 1) || // b2 (side A)
                (row === 6 && col === 6) || // g2 (side A)
                (row === 1 && col === 1) || // b7 (side B)
                (row === 1 && col === 6)    // g7 (side B)
            );
            if (!allowed) return;
            if (getPlayerTowerType() !== 'aggressive') return;
            if (Date.now() < getCooldownUntil(window.pieceDeployment?.playerSide || window.MY_SIDE || 'a')) return;

            const playerAllegiance = window.pieceDeployment?.playerSide || window.MY_SIDE || 'a';
            const towers = getTowersByAllegiance(playerAllegiance).filter(t => t.type === 'aggressive_tower' && !t.attack);
            const match = towers.find(t => t.position && t.position.row === row && t.position.col === col);
            if (!match) return;
            ability2Armed = true;
            if (ability2ArmTimeout) clearTimeout(ability2ArmTimeout);
            ability2ArmTimeout = setTimeout(() => {
                ability2Armed = false;
                ability2ArmTimeout = null;
            }, 1000);
        }

        document.addEventListener('click', (e) => {
            const cell = e.target.closest?.('.board-cell');
            if (!cell) return;
            armAbilityFromCell(cell);
        });

        document.addEventListener('keydown', (e) => {
            if (e.key !== 'Enter' || !ability2Armed) return;
            ability2Armed = false;
            const playerAllegiance = window.pieceDeployment?.playerSide || window.MY_SIDE || 'a';
            // prevent re-arming during active ability window
            setCooldownUntil(playerAllegiance, Date.now() + 3000);
            if (!isAuthority) {
                if (typeof window.postToParent === 'function') {
                    window.postToParent('state_update', {
                        type: 'state_update',
                        event: 'tower_ability_aggressive_request',
                        side: playerAllegiance
                    });
                }
                return;
            }

            runAggressiveAbility2(playerAllegiance, getPlayerTowerType);
            ability2Timer = setTimeout(() => {
                ability2Timer = null;
            }, 3000);
        });

        const playerAllegiance = window.pieceDeployment?.playerSide || window.MY_SIDE || 'a';
        applyToggleVisual(toggleElement, getPlayerTowerType(), playerAllegiance);
        updateToggleDisabled(toggleElement, playerAllegiance);
        const interval = setInterval(() => {
            const currentAllegiance = window.pieceDeployment?.playerSide || window.MY_SIDE || 'a';
            updateToggleDisabled(toggleElement, currentAllegiance);
        }, 300);
        toggleElement._aggAbilityInterval = interval;
    }

    window.AggressiveTowerAbility = {
        init,
        canSwitchTowers,
        rescaleTowerStats,
        getMaxHpForTower,
        updateToggleDisabled,
        applyToggleVisual,
        switchPlayerTowers,
        handleAbility2Request: handleAggressiveAbilityRequest,
        broadcastAggressiveAbility
    };
})();
