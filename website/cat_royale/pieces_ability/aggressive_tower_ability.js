// Ability logic for switching player towers between solid/aggressive.
// Exposes helpers on window.AggressiveTowerAbility for use in game_page.html.
(function() {
    function getMaxHpForTower(type) {
        if (type === 'solid' || type === 'solid_tower') return window.SolidTowerHP?.maxHP || 1000;
        if (type === 'aggressive' || type === 'aggressive_tower') return window.AggressiveTowerHP?.maxHP || 600;
        return 1000;
    }

    function getTowersByAllegiance(allegiance = 'a') {
        if (!window.pieceDeployment) return [];
        return (pieceDeployment.boardPieces || []).filter(p =>
            p.allegiance === allegiance &&
            (p.type === 'solid_tower' || p.type === 'aggressive_tower')
        );
    }

    function canSwitchTowers(allegiance = 'a') {
        if (typeof elixirManager === 'undefined') return false;
        if (elixirManager.currentElixir < 1) return false;
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
        towers.forEach(tower => {
            const prevMax = tower.maxHP || getMaxHpForTower(tower.type);
            const prevHp = tower.hp ?? prevMax;
            const ratio = prevMax ? Math.max(0, Math.min(prevHp / prevMax, 1)) : 1;
            const nextMax = getMaxHpForTower(registryType);
            tower.type = registryType;
            tower.maxHP = nextMax;
            tower.hp = Math.round(nextMax * ratio);
            refreshHealthBar(tower);
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
        const currentPlayerTowers = (state?.getCurrentPlayerTowers?.() || []).filter(Boolean);
        if (currentPlayerTowers.length === 0) return state?.getPlayerTowerType?.();
        if (!canSwitchTowers('a')) {
            console.log('Cannot switch towers: either under attack or not enough elixir.');
            return state?.getPlayerTowerType?.();
        }

        const currentType = currentPlayerTowers[0].dataset.towerType;
        const newType = currentType === 'solid' ? 'aggressive' : 'solid';
        const newImagePath = newType === 'solid'
            ? '../pieces/solid_tower/solid_tower.png'
            : '../pieces/agressive_tower/aggressive_tower.png';

        currentPlayerTowers.forEach(tower => {
            const img = tower.querySelector('img');
            if (img) img.src = newImagePath;
            tower.dataset.towerType = newType;
        });

        const playerTowers = getTowersByAllegiance('a');
        rescaleTowerStats(playerTowers, newType);

        // Deduct elixir
        elixirManager.currentElixir--;
        elixirManager.updateElixirDisplay();
        elixirManager.updateElixirBar();
        elixirManager.startElixirGeneration();

        console.log(`Switched towers to ${newType}. Elixir: ${elixirManager.currentElixir}`);
        state?.setPlayerTowerType?.(newType);
        applyToggleVisual(state?.toggleElement, newType);
        return newType;
    }

    function init(options = {}) {
        const toggleElement = options.toggleElement;
        if (!toggleElement) return;

        const getCurrentPlayerTowers = options.getCurrentPlayerTowers || (() => []);
        const getPlayerTowerType = options.getPlayerTowerType || (() => null);
        const setPlayerTowerType = options.setPlayerTowerType || (() => {});
        let ability2Armed = false;
        let ability2ArmTimeout = null;
        let ability2Timer = null;

        toggleElement.addEventListener('click', (e) => {
            e.stopPropagation();
            switchPlayerTowers({
                toggleElement,
                getCurrentPlayerTowers,
                getPlayerTowerType,
                setPlayerTowerType
            });
            // Arm ability 2 for 1s after single click when in aggressive mode
            const towerType = getPlayerTowerType();
            if (towerType === 'aggressive') {
                ability2Armed = true;
                if (ability2ArmTimeout) clearTimeout(ability2ArmTimeout);
                ability2ArmTimeout = setTimeout(() => {
                    ability2Armed = false;
                    ability2ArmTimeout = null;
                }, 1000);
            } else {
                ability2Armed = false;
                if (ability2ArmTimeout) {
                    clearTimeout(ability2ArmTimeout);
                    ability2ArmTimeout = null;
                }
            }
            // Immediately refresh clickable state in case elixir/attack status changed
            updateToggleDisabled(toggleElement, 'a');
        });

        document.addEventListener('keydown', (e) => {
            if (e.key !== 'Enter' || !ability2Armed) return;
            ability2Armed = false;
            const towerType = getPlayerTowerType();
            if (towerType !== 'aggressive') return;
            if (elixirManager.currentElixir <= 1) {
                console.log('Not enough elixir for aggressive ability (need >1).');
                return;
            }
            const towers = getTowersByAllegiance('a').filter(t => t.type === 'aggressive_tower');
            if (towers.length === 0) return;

            // Consume elixir
            elixirManager.currentElixir -= 1;
            elixirManager.updateElixirDisplay();
            elixirManager.updateElixirBar();
            elixirManager.startElixirGeneration();

            const forwardSlots = [
                { fromRow: 6, fromCol: 1, toRow: 5, toCol: 1 }, // b2 -> b3
                { fromRow: 6, fromCol: 6, toRow: 5, toCol: 6 }  // g2 -> g3
            ];

            towers.forEach(t => {
                // Apply 25% damage reduction
                t.damageReduction = 0.25;
                // Swap image to ability form
                const img = t.element ? t.element.querySelector('img') : null;
                if (img) {
                    t._originalImgSrc = t._originalImgSrc || img.src;
                    img.src = '../pieces/agressive_tower/aggressive_tower_ability_2.png';
                }
                const slot = forwardSlots.find(s => s.fromRow === t.position?.row && s.fromCol === t.position?.col);
                if (slot && window.pieceDeployment && typeof window.pieceDeployment.movePiece === 'function') {
                    t._originalPosition = { ...t.position };
                    window.pieceDeployment.movePiece(t.id, { row: slot.toRow, col: slot.toCol });
                    t.position = { row: slot.toRow, col: slot.toCol };
                }
            });

            if (ability2Timer) clearTimeout(ability2Timer);
            ability2Timer = setTimeout(() => {
                towers.forEach(t => {
                    t.damageReduction = 0;
                    // revert image
                    const img = t.element ? t.element.querySelector('img') : null;
                    if (img && t._originalImgSrc) {
                        img.src = t._originalImgSrc;
                    }
                    if (t._originalPosition && window.pieceDeployment && typeof window.pieceDeployment.movePiece === 'function') {
                        window.pieceDeployment.movePiece(t.id, { ...t._originalPosition });
                        t.position = { ...t._originalPosition };
                    }
                });
                ability2Timer = null;
            }, 5000);
        });

        applyToggleVisual(toggleElement, getPlayerTowerType());
        updateToggleDisabled(toggleElement, 'a');
        const interval = setInterval(() => updateToggleDisabled(toggleElement, 'a'), 300);
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
