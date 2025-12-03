// General registry for all cards/pieces and their target preferences.
// Exposed on window for non-module scripts.

const PieceRegistry = {
    shouter: {
        role: 'troop',
        targets: ['building', 'troop'],
    },
    solid_tower: {
        role: 'building',
        targets: ['troop'],
    },
    aggressive_tower: {
        role: 'building',
        targets: ['troop'],
    },
    king_tower: {
        role: 'building',
        targets: ['troop'],
    },
};

function isTargetable(attackerType, targetType) {
    const def = PieceRegistry[attackerType];
    if (!def) return false;
    return def.targets.includes(targetType);
}

function isKingTowerCellTargetable(targetEntry, allPieces = []) {
    if (!targetEntry || targetEntry.type !== 'king_tower') return true;
    const col = targetEntry.position?.col;
    const allegiance = targetEntry.allegiance;
    if (col === undefined || allegiance === undefined) return true;

    // Find alive side towers for that allegiance
    const towers = (allPieces || []).filter(p =>
        p &&
        p.allegiance === allegiance &&
        p.type &&
        p.type !== 'king_tower' &&
        p.type.includes('tower') &&
        (p.hp ?? p.maxHP ?? 0) > 0
    );

    const leftAlive = towers.some(p => p.position && p.position.col <= 3);
    const rightAlive = towers.some(p => p.position && p.position.col >= 4);

    // King tower cells are col 3 (left) and 4 (right)
    if (col === 3 && leftAlive) return false;
    if (col === 4 && rightAlive) return false;
    return true;
}

function isCellBlocked(row, col) {
    const blocked = new Set([
        // Blocked squares: b2, b7, g2, g7, d2, d1, d7, d8, e2, e1, e7, e8
        '6,1', '1,1',            // b2, b7
        '6,6', '1,6',            // g2, g7
        '6,3', '7,3', '1,3', '0,3', // d2, d1, d7, d8
        '6,4', '7,4', '1,4', '0,4'  // e2, e1, e7, e8
    ]);
    return blocked.has(`${row},${col}`);
}

window.PieceRegistry = PieceRegistry;
window.isTargetable = isTargetable;
window.isKingTowerCellTargetable = isKingTowerCellTargetable;
window.isCellBlocked = isCellBlocked;
