// General registry for all cards/pieces and their target preferences.
// Exposed on window for non-module scripts.

const PieceRegistry = {
    shouter: {
        role: 'troop',
        targets: ['building', 'troop'],
    },
    fighter: {
        role: 'troop',
        targets: ['building', 'troop'],
    },
    squirmer: {
        role: 'troop',
        targets: ['building'],
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
    ruler: {
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

    // Guard towers:
    // allegiance 'b' (top): b7 -> row 1, col 1 guards d7/d8 (col 3); g7 -> row 1, col 6 guards e7/e8 (col 4)
    // allegiance 'a' (bottom): b2 -> row 6, col 1 guards d1/d2 (col 3); g2 -> row 6, col 6 guards e1/e2 (col 4)
    const guardRow = allegiance === 'b' ? 1 : 6;
    const leftGuard = (allPieces || []).find(p =>
        p &&
        p.allegiance === allegiance &&
        p.type &&
        p.type !== 'king_tower' &&
        p.type.includes('tower') &&
        p.position &&
        p.position.row === guardRow &&
        p.position.col === 1 &&
        (p.hp ?? p.maxHP ?? 0) > 0
    );
    const rightGuard = (allPieces || []).find(p =>
        p &&
        p.allegiance === allegiance &&
        p.type &&
        p.type !== 'king_tower' &&
        p.type.includes('tower') &&
        p.position &&
        p.position.row === guardRow &&
        p.position.col === 6 &&
        (p.hp ?? p.maxHP ?? 0) > 0
    );

    if (col === 3 && leftGuard) return false;
    if (col === 4 && rightGuard) return false;
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
