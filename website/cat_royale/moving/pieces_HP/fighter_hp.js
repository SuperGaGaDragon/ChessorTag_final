// Fighter HP definition and health bar helper.
// Max HP: 180
(function() {
    const maxHP = 180;
    const barColor = '#DD2222';

    function createHealthBar(container) {
        if (!container) return null;
        let state = null;
        const barWrapper = document.createElement('div');
        barWrapper.style.position = 'absolute';
        barWrapper.style.left = '10%';
        barWrapper.style.right = '10%';
        barWrapper.style.bottom = '4px';
        barWrapper.style.height = '12px';
        barWrapper.style.background = 'rgba(0,0,0,0.2)';
        barWrapper.style.border = '1px solid #000';
        barWrapper.style.borderRadius = '4px';
        barWrapper.style.overflow = 'hidden';
        barWrapper.style.pointerEvents = 'auto';
        barWrapper.style.zIndex = '99999';
        barWrapper.style.cursor = 'default';

        const barFill = document.createElement('div');
        barFill.style.height = '100%';
        barFill.style.width = '100%';
        barFill.style.background = barColor;
        barFill.style.transition = 'width 0.15s linear';
        barFill.style.pointerEvents = 'none';

        const barLabel = document.createElement('div');
        barLabel.style.position = 'absolute';
        barLabel.style.left = '50%';
        barLabel.style.top = '50%';
        barLabel.style.transform = 'translate(-50%, -50%)';
        barLabel.style.width = '100%';
        barLabel.style.textAlign = 'center';
        barLabel.style.fontSize = '10px';
        barLabel.style.fontWeight = 'bold';
        barLabel.style.color = '#fff';
        barLabel.style.textShadow = '0 0 2px #000';
        barLabel.style.pointerEvents = 'none';

        barWrapper.appendChild(barFill);
        barWrapper.appendChild(barLabel);
        container.style.position = 'relative';
        container.appendChild(barWrapper);

        function refreshLabel() {
            if (!state) return;
            barLabel.textContent = state.isHovering ? `${state.current}/${maxHP}` : `${state.current}`;
        }

        state = {
            max: maxHP,
            current: maxHP,
            isHovering: false,
            barWrapper,
            barFill,
            barLabel,
            update(currentHP) {
                state.current = Math.max(0, Math.min(currentHP, maxHP));
                const ratio = state.current / maxHP;
                barFill.style.width = `${ratio * 100}%`;
                refreshLabel();
            }
        };

        barWrapper.addEventListener('mouseenter', () => {
            state.isHovering = true;
            refreshLabel();
        });
        barWrapper.addEventListener('mouseleave', () => {
            state.isHovering = false;
            refreshLabel();
        });
        barWrapper.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
        });

        refreshLabel();
        return state;
    }

    window.FighterHP = {
        maxHP,
        createHealthBar
    };
})();
