// Game end watcher: if any king tower HP reaches 0, freeze UI and show overlay.
(function() {
    const CHECK_MS = 250;
    let overlay = null;
    let blocker = null;
    let checkTimer = null;

    function stopInteractions() {
        if (window.pieceDeployment && window.pieceDeployment.attackScanTimer) {
            clearInterval(window.pieceDeployment.attackScanTimer);
            window.pieceDeployment.attackScanTimer = null;
        }
        window.gameOver = true;
        const block = document.createElement('div');
        block.style.position = 'fixed';
        block.style.inset = '0';
        block.style.zIndex = '99998';
        block.style.background = 'transparent';
        block.style.pointerEvents = 'auto';
        document.body.appendChild(block);
        blocker = block;
    }

    function showOverlay() {
        if (overlay) return;
        overlay = document.createElement('div');
        overlay.style.position = 'fixed';
        overlay.style.inset = '0';
        overlay.style.display = 'flex';
        overlay.style.alignItems = 'center';
        overlay.style.justifyContent = 'center';
        overlay.style.background = 'rgba(0,0,0,0)';
        overlay.style.transition = 'background 0.6s ease';
        overlay.style.zIndex = '99999';
        overlay.style.pointerEvents = 'none';

        const dialog = document.createElement('div');
        dialog.style.display = 'flex';
        dialog.style.alignItems = 'center';
        dialog.style.gap = '16px';
        dialog.style.padding = '12px 18px';
        dialog.style.borderRadius = '10px';
        dialog.style.background = 'rgba(255,255,255,0.9)';
        dialog.style.boxShadow = '0 8px 24px rgba(0,0,0,0.35)';
        dialog.style.pointerEvents = 'auto';

        const img = document.createElement('img');
        img.style.width = '80px';
        img.style.height = '80px';
        img.style.objectFit = 'contain';
        img.style.borderRadius = '8px';
        img.style.background = '#fff';
        img.alt = 'Game End';
        img.src = '../pieces/shouter/shouter_board.png';

        const bubble = document.createElement('div');
        bubble.textContent = 'Game Ends';
        bubble.style.padding = '10px 14px';
        bubble.style.borderRadius = '8px';
        bubble.style.background = '#f5f5f5';
        bubble.style.border = '2px solid #000';
        bubble.style.fontSize = '18px';
        bubble.style.fontWeight = '900';
        bubble.style.color = '#111';
        bubble.style.boxShadow = '2px 2px 0 #000';

        dialog.appendChild(img);
        dialog.appendChild(bubble);
        overlay.appendChild(dialog);
        document.body.appendChild(overlay);

        // Delay fade to dark to preserve final frame for 1s
        setTimeout(() => {
            overlay.style.background = 'rgba(0,0,0,0.65)';
        }, 1000);
    }

    function triggerGameEnd() {
        if (window.gameEndsTriggered) return;
        window.gameEndsTriggered = true;
        stopInteractions();
        showOverlay();
        if (checkTimer) clearInterval(checkTimer);
    }

    function hasKingDown(shared) {
        if (!shared) return false;
        const aDead = shared.a && typeof shared.a.hp === 'number' && shared.a.hp <= 0;
        const bDead = shared.b && typeof shared.b.hp === 'number' && shared.b.hp <= 0;
        return aDead || bDead;
    }

    function check() {
        if (window.gameEndsTriggered) return;
        const pd = window.pieceDeployment;
        if (!pd || !pd.kingTowerShared) return;
        if (hasKingDown(pd.kingTowerShared)) {
            triggerGameEnd();
        }
    }

    checkTimer = setInterval(check, CHECK_MS);
})();
