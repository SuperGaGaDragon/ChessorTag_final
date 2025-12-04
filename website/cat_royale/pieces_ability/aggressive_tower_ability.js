// Ability logic for switching player towers between solid/aggressive.
// Exposes helpers on window.AggressiveTowerAbility for use in game_page.html.
(function() {
    function ensureAbilityState() {
        if (!window.TowerAbilityState) {
            window.TowerAbilityState = { solidActive: false, aggressiveActive: false };
        }
        return window.TowerAbilityState;
    }

    function setAbilityLock(key, active) {
        const state = ensureAbilityState();
        state[key] = !!active;
    }

    function isAnyAbilityActive() {
        const state = window.TowerAbilityState;
        return !!(state?.solidActive || state?.aggressiveActive);
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
        if (isAnyAbilityActive()) return false;
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
        if (tower.healthBar && tower.healthBar.barWrapper && tower.healthBar.barWrapper.parentElement) {
            tower.healthBar.barWrapper.remove();
        }
        let factory = null;
        if (tower.type === 'aggressive_tower') factory = window.AggressiveTowerHP?.createHealthBar;
        if (tower.type === 'solid_tower') factory = window.SolidTowerHP?.createHealthBar;
        if (typeof factory === 'function') {
            tower.healthBar = factory(anchor);
            if (tower.healthBar && typeof tower.healthBar.update === 'function') {
                tower.healthBar.update(tower.hp);
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

    function applyToggleVisual(toggleEl, playerTowerType) {
        if (!toggleEl) return;
        const img1 = toggleEl.querySelector('.tower-img-1');
        const img2 = toggleEl.querySelector('.tower-img-2');
        if (!img1 || !img2) return;
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
        const newImagePath = newType === 'solid'
            ? '../pieces/solid_tower/solid_tower.png'
            : '../pieces/agressive_tower/aggressive_tower.png';

        if (!elixirManager.spend(1, playerAllegiance)) {
            console.log('Cannot switch towers: insufficient elixir for host');
            return state?.getPlayerTowerType?.();
        }

        currentPlayerTowers.forEach(tower => {
            const img = tower.querySelector('img');
            if (img) img.src = newImagePath;
            tower.dataset.towerType = newType;
        });

        const playerTowers = getTowersByAllegiance(playerAllegiance);
        rescaleTowerStats(playerTowers, newType);

        console.log(`[AggressiveTowerAbility] Switched ${playerAllegiance} towers to ${newType}. Elixir: ${elixirManager.currentElixir}`);
        state?.setPlayerTowerType?.(newType);
        applyToggleVisual(state?.toggleElement, newType);
        if (typeof window.postToParent === 'function') {
            const serialized = playerTowers.map(t => ({
                id: t.id,
                row: t.position?.row,
                col: t.position?.col,
                type: t.type,
                hp: t.hp,
                max_hp: t.maxHP,
                allegiance: t.allegiance,
                board_image_path: t.boardImagePath
            }));
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
        let abilityCooldownUntil = 0;

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

        if (!isAuthority) {
            return;
        }

        if (isAuthority) {
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
                if (Date.now() < abilityCooldownUntil) return;

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
                const towerType = getPlayerTowerType();
                if (towerType !== 'aggressive') return;
                if (!elixirManager.hasEnough(2, playerAllegiance)) {
                    console.log('Not enough elixir for aggressive ability (need >1).');
                    return;
                }

                const playerAllegiance = window.pieceDeployment?.playerSide || window.MY_SIDE || 'a';
                const towers = getTowersByAllegiance(playerAllegiance).filter(t => t.type === 'aggressive_tower' && !t.attack);
                if (towers.length === 0) return;

                if (!elixirManager.spend(1, playerAllegiance)) {
                    console.log('Spend failed for aggressive ability.');
                    return;
                }

                setAbilityLock('aggressiveActive', true);

                // Forward slots depend on allegiance
                // Side A: b2->b3, g2->g3 (row 6->5)
                // Side B: b7->b6, g7->g6 (row 1->2)
                const forwardSlots = playerAllegiance === 'a'
                    ? [
                        { fromRow: 6, fromCol: 1, toRow: 5, toCol: 1 }, // b2 -> b3
                        { fromRow: 6, fromCol: 6, toRow: 5, toCol: 6 }  // g2 -> g3
                      ]
                    : [
                        { fromRow: 1, fromCol: 1, toRow: 2, toCol: 1 }, // b7 -> b6
                        { fromRow: 1, fromCol: 6, toRow: 2, toCol: 6 }  // g7 -> g6
                      ];

                towers.forEach(t => {
                    // Apply 25% damage reduction
                    t.damageReduction = 0.25;
                    // Swap image to ability form
                    const img = t.element ? t.element.querySelector('img') : null;
                    if (img) {
                        t._aggOriginalImgSrc = t._aggOriginalImgSrc || img.src;
                        img.src = '../pieces/agressive_tower/aggressive_tower_ability_2.png';
                    }
                    const slot = forwardSlots.find(s => s.fromRow === t.position?.row && s.fromCol === t.position?.col);
                    if (slot && window.pieceDeployment && typeof window.pieceDeployment.movePiece === 'function') {
                        t._originalPosition = { ...t.position };
                        window.pieceDeployment.movePiece(t.id, { row: slot.toRow, col: slot.toCol });
                        t.position = { row: slot.toRow, col: slot.toCol };
                    }
                });

                console.log(`[AggressiveTowerAbility] Activated ability for ${playerAllegiance} towers`);

                if (ability2Timer) clearTimeout(ability2Timer);
                ability2Timer = setTimeout(() => {
                    towers.forEach(t => {
                        t.damageReduction = 0;
                        // revert image
                        const img = t.element ? t.element.querySelector('img') : null;
                        if (img) {
                            const fallback = '../pieces/agressive_tower/aggressive_tower.png';
                            img.src = t._aggOriginalImgSrc || fallback;
                        }
                        if (t._originalPosition && window.pieceDeployment && typeof window.pieceDeployment.movePiece === 'function') {
                            window.pieceDeployment.movePiece(t.id, { ...t._originalPosition });
                            t.position = { ...t._originalPosition };
                        }
                    });
                    ability2Timer = null;
                    abilityCooldownUntil = Date.now() + 5000; // 5s cooldown after effect ends
                    setAbilityLock('aggressiveActive', false);
                }, 3000);
            });
        }

        applyToggleVisual(toggleElement, getPlayerTowerType());

        const playerAllegiance = window.pieceDeployment?.playerSide || window.MY_SIDE || 'a';
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
        switchPlayerTowers
    };
})();
