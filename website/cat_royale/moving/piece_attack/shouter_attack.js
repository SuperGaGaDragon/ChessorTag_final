// Shouter attack helpers (non-module, exposed on window).
// Defines attack range and handles stopping movement + shake animation.

function isInShouterAttackRange(shouter, target) {
    if (!shouter || !target || !target.position) return false;
    const dr = Math.abs((shouter.position?.row ?? 0) - target.position.row);
    const dc = Math.abs((shouter.position?.col ?? 0) - target.position.col);
    // Queen-like, but max 2 tiles: horizontal / vertical / diagonal up to 2
    const inRow = dr === 0 && dc > 0 && dc <= 2;
    const inCol = dc === 0 && dr > 0 && dr <= 2;
    const inDiag = dr === dc && dr > 0 && dr <= 2;
    return inRow || inCol || inDiag;
}

function startShouterAttack(shouter, target) {
    // Only HOST executes attack logic
    if (window.IS_HOST !== true) {
        console.log('[shouter_attack] CLIENT mode: skip attack execution');
        return;
    }

    if (!shouter || !shouter.element) return;
    if (shouter.shouter_lived === false || (shouter.hp !== undefined && shouter.hp <= 0)) return;
    if (shouter._attackInterval) {
        clearInterval(shouter._attackInterval);
        shouter._attackInterval = null;
    }
    shouter.attack = true;
    shouter.currentTargetId = target?.id || null;

    // Clear any prior shake
    shouter.element.classList.remove('shouter-attack-shake');
    // Start shake
    shouter.element.classList.add('shouter-attack-shake');

    // Emit attack glyphs toward target
    const glyphs = ['*', '&', '%', '¥', '#', '!', '?'];
    let glyphIndex = 0;
    const attempt = () => {
        if (!shouter.attack || !target || !target.position || (shouter.shouter_lived === false) || (shouter.hp !== undefined && shouter.hp <= 0) || (target.hp !== undefined && target.hp <= 0) || target.shouter_lived === false) {
            shouter.attack = false;
            shouter.currentTargetId = null;
            if (shouter._mover && typeof shouter._mover.startAutoMove === 'function') {
                shouter._mover.startAutoMove();
            }
            return false;
        }
        const glyph = glyphs[glyphIndex % glyphs.length];
        glyphIndex++;
        spawnAttackGlyph(shouter, target, glyph, () => {
            if (window.pieceDeployment) window.pieceDeployment.applyDamage(target, 75, shouter);
        });
        return true;
    };

    // Fire immediately once target acquired
    attempt();

    shouter._attackInterval = setInterval(() => {
        if (!attempt()) {
            clearInterval(shouter._attackInterval);
            shouter._attackInterval = null;
            return;
        }
    }, 500);
}

window.isInShouterAttackRange = isInShouterAttackRange;
window.startShouterAttack = startShouterAttack;

// Internal helper to animate a flying glyph
function spawnAttackGlyph(shouterEntry, targetEntry, glyphChar, onHit) {
    const fromEl = shouterEntry?.element;
    const toEl = targetEntry?.element;
    const toCell = document.querySelector(`.board-cell[data-row="${targetEntry?.position?.row}"][data-col="${targetEntry?.position?.col}"]`);
    const fromCell = document.querySelector(`.board-cell[data-row="${shouterEntry?.position?.row}"][data-col="${shouterEntry?.position?.col}"]`);
    const fromNode = fromEl || fromCell;
    const toNode = toEl || toCell;
    if (!fromNode || !toNode) return;

    const glyph = document.createElement('div');
    glyph.textContent = glyphChar;
    glyph.style.position = 'fixed';
    glyph.style.zIndex = '9998';
    glyph.style.fontSize = '28px';
    glyph.style.fontWeight = 'bold';
    glyph.style.color = '#000';
    glyph.style.pointerEvents = 'none';

    const fromRect = fromNode.getBoundingClientRect();
    const toRect = toNode.getBoundingClientRect();
    glyph.style.left = (fromRect.left + fromRect.width / 2) + 'px';
    glyph.style.top = (fromRect.top + fromRect.height / 2) + 'px';

    document.body.appendChild(glyph);

    const deltaX = (toRect.left + toRect.width / 2) - (fromRect.left + fromRect.width / 2);
    const deltaY = (toRect.top + toRect.height / 2) - (fromRect.top + fromRect.height / 2);

    glyph.animate([
        { transform: 'translate(0px, 0px)', opacity: 1 },
        { transform: `translate(${deltaX}px, ${deltaY}px)`, opacity: 0.2 }
    ], {
        duration: 800,
        easing: 'linear',
        fill: 'forwards'
    }).onfinish = () => {
        glyph.remove();
        if (typeof onHit === 'function') onHit();
    };
}
