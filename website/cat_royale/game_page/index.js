(function () {
    const state = {
        ws: null,
        gameId: null,
        side: null,
        spectator: false,
        playersConnected: false,
        opponentReady: false,
        ui: {},
    };

    function cacheUI() {
        state.ui.createBtn = document.getElementById('create-btn');
        state.ui.joinBtn = document.getElementById('join-btn');
        state.ui.joinInput = document.getElementById('game-id-input');
        state.ui.startBtn = document.getElementById('start-btn');
        state.ui.sidePill = document.getElementById('side-pill');
        state.ui.opponentText = document.getElementById('opponent-text');
        state.ui.status = document.getElementById('status-text');
        state.ui.link = document.getElementById('link-text');
        state.ui.gameFrame = document.getElementById('game-frame');
    }

    function setStatus(text) {
        if (state.ui.status) state.ui.status.textContent = text;
    }

    function setSide(side) {
        state.side = side;
        state.spectator = side === 'spectate';
        if (state.ui.sidePill) {
            state.ui.sidePill.textContent = side ? `Side: ${side.toUpperCase()}` : 'Side: -';
        }
        updateStartButton();
    }

    function setOpponentReady(ready, label = null) {
        state.opponentReady = ready;
        if (!state.ui.opponentText) return;
        const text = ready ? 'Opponent: ready' : 'Opponent: not ready';
        state.ui.opponentText.textContent = label ? `${text} (${label})` : text;
        state.ui.opponentText.style.color = ready ? '#2F5233' : '#8B5CF6';
    }

    function updateLink() {
        if (!state.ui.link) return;
        if (!state.gameId) {
            state.ui.link.textContent = '';
            return;
        }
        const base = `${window.location.origin}${window.location.pathname}`;
        const url = `${base}?game=${state.gameId}`;
        state.ui.link.textContent = `Share link: ${url}`;
        if (window.history?.replaceState) {
            window.history.replaceState({}, '', `?game=${state.gameId}`);
        }
    }

    function updateStartButton() {
        if (!state.ui.startBtn) return;
        if (state.spectator) {
            state.ui.startBtn.disabled = true;
            state.ui.startBtn.textContent = 'Spectating';
            return;
        }
        const can = state.playersConnected && state.side && state.side !== 'spectate';
        state.ui.startBtn.disabled = !can;
        state.ui.startBtn.textContent = can ? 'Start' : 'Waiting';
    }

    function apiBase() {
        if (window.location.hostname === 'chessortag.org' || window.location.hostname === 'www.chessortag.org') {
            return 'https://api.chessortag.org';
        }
        return '';
    }

    function buildWsUrl(gameId) {
        const isProd = window.location.hostname === 'chessortag.org' || window.location.hostname === 'www.chessortag.org';
        if (isProd) {
            return `wss://api.chessortag.org/ws/battle/${gameId}`;
        }
        const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
        return `${proto}://${window.location.host}/ws/battle/${gameId}`;
    }

    function cleanupSocket() {
        if (state.ws) {
            try { state.ws.close(); } catch (err) { /* ignore */ }
        }
        state.ws = null;
    }

    function forwardToFrame(type, payload = {}) {
        if (state.ui.gameFrame && state.ui.gameFrame.contentWindow) {
            state.ui.gameFrame.contentWindow.postMessage({ type, payload }, '*');
        }
    }

    function handleStart(msg) {
        setStatus('Battle started!');
        if (state.ui.startBtn) state.ui.startBtn.disabled = true;
        if (state.ui.gameFrame) state.ui.gameFrame.classList.remove('hidden');
        forwardToFrame('battle_start', msg);
    }

    function handleMessage(event) {
        try {
            const msg = JSON.parse(event.data);
            switch (msg.type) {
                case 'side':
                    setSide(msg.side);
                    setStatus(`Connected. You are ${msg.side.toUpperCase()}`);
                    forwardToFrame('side_update', { side: msg.side });
                    break;
                case 'deploy_request':
                    forwardToFrame('deploy_request', msg);
                    break;
                case 'state_update':
                    forwardToFrame('state_update', msg);
                    break;
                case 'players_connected':
                    state.playersConnected = true;
                    setStatus('Opponent joined. Click Start when ready.');
                    updateStartButton();
                    break;
                case 'opponent_ready':
                    setOpponentReady(true, msg.tower);
                    break;
                case 'start':
                    handleStart(msg);
                    break;
                case 'deploy':
                    forwardToFrame('remote_deploy', msg);
                    break;
                case 'ruler_move':
                    forwardToFrame('remote_ruler_move', msg);
                    break;
                case 'ruler_move_request':
                    forwardToFrame('ruler_move_request', msg);
                    break;
                case 'opponent_disconnected':
                    setStatus('Opponent disconnected');
                    state.playersConnected = false;
                    updateStartButton();
                    forwardToFrame('opponent_disconnected', msg);
                    break;
                case 'error':
                    setStatus(msg.error || 'Unknown error');
                    break;
                default:
                    break;
            }
        } catch (err) {
            console.error('Failed to parse WS message', err);
        }
    }

    function connectWs(gameId) {
        cleanupSocket();
        const url = buildWsUrl(gameId);
        console.log('[battle] connecting WS:', url);
        const ws = new WebSocket(url);
        state.ws = ws;
        window.battleSocket = ws;

        ws.onopen = () => {
            if (ws !== state.ws) return;
            console.log('[battle] WS open');
            setStatus('WebSocket connected');
            updateStartButton();
        };

        ws.onmessage = (event) => {
            if (ws !== state.ws) return;
            console.log('[battle] WS message', event.data);
            handleMessage(event);
        };

        ws.onclose = (ev) => {
            if (ws !== state.ws) return;
            console.log('[battle] WS closed', ev.code, ev.reason);
            setStatus('WebSocket closed');
            updateStartButton();
        };

        ws.onerror = (err) => {
            if (ws !== state.ws) return;
            console.error('[battle] WS error', err);
            setStatus('WebSocket error');
        };
    }

    async function createGame() {
        try {
            const res = await fetch(`${apiBase()}/api/battle/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
            });
            if (!res.ok) throw new Error('Failed to create game');
            const data = await res.json();
            state.gameId = data.game_id;
            updateLink();
            setStatus('Wait for opponent to join');
            connectWs(state.gameId);
        } catch (err) {
            console.error(err);
            setStatus('Create game failed');
        }
    }

    async function joinGame(gameId) {
        if (!gameId) return;
        gameId = gameId.trim().toUpperCase();
        state.gameId = gameId;
        updateLink();
        setStatus('Joining game...');
        setOpponentReady(false, null);
        try {
            const res = await fetch(`${apiBase()}/api/battle/join`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ game_id: gameId }),
            });
            if (!res.ok) throw new Error('Join failed');
            const data = await res.json();
            if (data.side) {
                setSide(data.side);
            }
            connectWs(gameId);
            setStatus(data.side === 'spectate' ? 'Joined as spectator' : 'Waiting for opponent...');
        } catch (err) {
            console.error(err);
            setStatus('Join failed: game not found or full');
        }
    }

    function sendReady() {
        if (!state.ws || state.ws.readyState !== WebSocket.OPEN) {
            setStatus('WebSocket not connected');
            return;
        }
        if (state.spectator) return;
        state.ws.send(JSON.stringify({ type: 'ready', tower: 'solid' }));
        setStatus('Ready sent. Waiting for opponent...');
        setOpponentReady(false, null);
        if (state.ui.startBtn) state.ui.startBtn.disabled = true;
    }

    function sendDeployRequest(payload) {
        if (!state.ws || state.ws.readyState !== WebSocket.OPEN) {
            console.error('[PAGE] sendDeployRequest: WebSocket not open!', state.ws?.readyState);
            return;
        }
        const message = {
            type: 'deploy_request',
            game_id: state.gameId,
            row: payload.row,
            col: payload.col,
            pieceType: payload.pieceType,
            allegiance: payload.allegiance || state.side,
            cost: payload.cost,
            boardImagePath: payload.boardImagePath,
        };
        console.log('[PAGE → WS] sending deploy_request', message);
        state.ws.send(JSON.stringify(message));
        // Host should also process locally without waiting for echo
        if (state.side === 'a') {
            forwardToFrame('deploy_request', message);
        }
    }

    function sendRulerMove(payload) {
        if (!state.ws || state.ws.readyState !== WebSocket.OPEN) {
            console.error('[PAGE] sendRulerMove: WebSocket not open!', state.ws?.readyState);
            return;
        }
        const message = {
            type: 'ruler_move_request',
            id: payload.id,
            row: payload.row,
            col: payload.col,
            allegiance: payload.allegiance || state.side,
        };
        console.log('[PAGE → WS] sending ruler_move_request', message);
        state.ws.send(JSON.stringify(message));
        if (state.side === 'a') {
            forwardToFrame('ruler_move_request', message);
        }
    }

    function handleQueryJoin() {
        const params = new URLSearchParams(window.location.search);
        const game = params.get('game');
        if (game) {
            if (state.ui.joinInput) state.ui.joinInput.value = game;
            joinGame(game);
        }
    }

    function bindUI() {
        if (state.ui.createBtn) {
            state.ui.createBtn.addEventListener('click', (e) => {
                e.preventDefault();
                createGame();
            });
        }
        if (state.ui.joinBtn) {
            state.ui.joinBtn.addEventListener('click', (e) => {
                e.preventDefault();
                const value = state.ui.joinInput?.value?.trim();
                joinGame(value);
            });
        }
        if (state.ui.startBtn) {
            state.ui.startBtn.addEventListener('click', (e) => {
                e.preventDefault();
                sendReady();
            });
        }
    }

    function bindFrameMessages() {
        console.log('[PAGE] bindFrameMessages registered');
        window.addEventListener('message', (event) => {
            const msg = event.data || {};
            console.log('[PAGE raw message]', event.origin, event.data);
            switch (msg.type) {
                case 'deploy_request':
                    console.log('[PAGE] handling deploy_request');
                    sendDeployRequest(msg.payload || msg);
                    break;
                case 'local_ruler_move':
                    console.log('[PAGE] handling local_ruler_move');
                    sendRulerMove(msg.payload || msg);
                    break;
                case 'state_update':
                    console.log('[PAGE] handling state_update');
                    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
                        const payload = {
                            ...msg.payload,
                            type: 'state_update',
                        };
                        console.log('[PAGE → WS] sending state_update', payload);
                        state.ws.send(JSON.stringify(payload));
                    }
                    break;
                default:
                    console.log('[PAGE] unhandled message type:', msg.type);
                    break;
            }
        });
    }

    function init() {
        console.log('[PAGE] init top', window.location.href);
        cacheUI();
        bindUI();
        bindFrameMessages();
        updateStartButton();
        handleQueryJoin();
    }

    init();
})();
