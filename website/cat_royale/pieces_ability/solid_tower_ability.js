// Solid tower ability: click tower at b2 or b7 when in solid mode, press Enter within 1s.
// Effect: for 3s, damage received reduced by 75% and image switches to ability skin.
(function() {
    const ABILITY_IMG = '../pieces/solid_tower/solid_tower_ability.png';
    const ARM_WINDOW_MS = 1000;
    const DURATION_MS = 3000;
    const COOLDOWN_MS = 5000;
    const ABILITY_COST = 1;
    let armed = false;
    let armTimer = null;
    let cooldownUntil = 0;
    let activeTimers = new Map(); // towerId -> timeout

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

    function isSolidMode(getPlayerTowerType) {
        return typeof getPlayerTowerType === 'function' && getPlayerTowerType() === 'solid';
    }

    function allowedCell(cell) {
        if (!cell) return false;
        const row = parseInt(cell.dataset.row, 10);
        const col = parseInt(cell.dataset.col, 10);
        return (
            (row === 6 && col === 1) || // b2
            (row === 6 && col === 6) || // g2
            (row === 1 && col === 1) || // b7
            (row === 1 && col === 6)    // g7
        );
    }

    function findSolidTowerAt(row, col, allegiance) {
        if (!window.pieceDeployment) return null;
        return (pieceDeployment.boardPieces || []).find(p =>
            p.allegiance === allegiance &&
            p.type === 'solid_tower' &&
            p.position &&
            p.position.row === row &&
            p.position.col === col &&
            (p.hp ?? p.maxHP ?? 1) > 0
        );
    }

    function applyAbility(tower) {
        if (!tower) return;
        tower.damageReduction = 0.75;
        const img = tower.element ? tower.element.querySelector('img') : null;
        if (img) {
            tower._originalImgSrc = tower._originalImgSrc || img.src;
            img.src = ABILITY_IMG;
        }
        tower.boardImagePath = ABILITY_IMG;

        if (activeTimers.has(tower.id)) {
            clearTimeout(activeTimers.get(tower.id));
        }
        const timeout = setTimeout(() => {
            tower.damageReduction = 0;
            const revertImg = tower.element ? tower.element.querySelector('img') : null;
            if (revertImg && tower._originalImgSrc) {
                revertImg.src = tower._originalImgSrc;
            }
            tower.boardImagePath = tower._originalImgSrc || tower.boardImagePath;
            activeTimers.delete(tower.id);
        }, DURATION_MS);
        activeTimers.set(tower.id, timeout);
    }

    function triggerSolidAbility(playerAllegiance, getPlayerTowerType) {
        if (!isSolidMode(getPlayerTowerType)) return false;
        if (Date.now() < cooldownUntil) return false;

        // Apply to both player towers if present
        const targets = [];
        const row = playerAllegiance === 'a' ? 6 : 1;
        const tLeft = findSolidTowerAt(row, 1, playerAllegiance);
        const tRight = findSolidTowerAt(row, 6, playerAllegiance);
        if (tLeft) targets.push(tLeft);
        if (tRight) targets.push(tRight);
        if (targets.length === 0) return false;

        if (!elixirManager.hasEnough(ABILITY_COST, playerAllegiance)) {
            console.log('Not enough elixir for solid ability.');
            if (typeof window.postToParent === 'function') {
                window.postToParent('state_update', {
                    type: 'state_update',
                    event: 'error',
                    code: 'elixir_insufficient',
                    side: playerAllegiance,
                    action: 'tower_ability_solid',
                    cost: ABILITY_COST
                });
            }
            return false;
        }
        if (!elixirManager.spend(ABILITY_COST, playerAllegiance)) {
            console.log('Solid ability spend failed.');
            return false;
        }

        setAbilityLock('solidActive', true);
        targets.forEach(applyAbility);
        cooldownUntil = Date.now() + COOLDOWN_MS;
        if (typeof window.postToParent === 'function') {
            window.postToParent('state_update', {
                type: 'state_update',
                event: 'tower_ability_solid',
                side: playerAllegiance,
                targets: targets.map(t => ({
                    id: t.id,
                    row: t.position?.row,
                    col: t.position?.col,
                    allegiance: t.allegiance
                })),
                duration_ms: DURATION_MS
            });
        }

        console.log(`[SolidTowerAbility] Activated ability for ${playerAllegiance} towers`);

        setTimeout(() => {
            setAbilityLock('solidActive', false);
        }, DURATION_MS);

        return true;
    }

    function handleSolidAbilityRequest(side, getPlayerTowerType) {
        const playerAllegiance = side || window.pieceDeployment?.playerSide || window.MY_SIDE || 'a';
        if (window.IS_HOST !== true) {
            if (typeof window.postToParent === 'function') {
                window.postToParent('state_update', {
                    type: 'state_update',
                    event: 'tower_ability_solid_request',
                    side: playerAllegiance
                });
            }
            return false;
        }
        return triggerSolidAbility(playerAllegiance, getPlayerTowerType);
    }

    function init(options = {}) {
        const getPlayerTowerType = options.getPlayerTowerType || (() => null);
        document.addEventListener('click', (e) => {
            const cell = e.target.closest?.('.board-cell');
            if (!cell) return;
            if (!isSolidMode(getPlayerTowerType)) return;
            if (!allowedCell(cell)) return;
            if (Date.now() < cooldownUntil) return;
            const row = parseInt(cell.dataset.row, 10);
            const col = parseInt(cell.dataset.col, 10);

            const playerAllegiance = window.pieceDeployment?.playerSide || window.MY_SIDE || 'a';
            const tower = findSolidTowerAt(row, col, playerAllegiance);
            if (!tower) return;
            armed = true;
            if (armTimer) clearTimeout(armTimer);
            armTimer = setTimeout(() => {
                armed = false;
                armTimer = null;
            }, ARM_WINDOW_MS);
        });

        document.addEventListener('keydown', (e) => {
            if (e.key !== 'Enter' || !armed) return;
            armed = false;
            if (armTimer) {
                clearTimeout(armTimer);
                armTimer = null;
            }
            const playerAllegiance = window.pieceDeployment?.playerSide || window.MY_SIDE || 'a';
            if (!isSolidMode(getPlayerTowerType)) return;
            if (Date.now() < cooldownUntil) return;
            if (window.IS_HOST !== true) {
                if (typeof window.postToParent === 'function') {
                    window.postToParent('state_update', {
                        type: 'state_update',
                        event: 'tower_ability_solid_request',
                        side: playerAllegiance
                    });
                }
                return;
            }
            triggerSolidAbility(playerAllegiance, getPlayerTowerType);
        });
    }

    window.SolidTowerAbility = {
        init,
        handleRequest: handleSolidAbilityRequest
    };
})();
