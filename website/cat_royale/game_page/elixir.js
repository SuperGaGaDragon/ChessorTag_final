// Elixir Management System
class ElixirManager {
    constructor() {
        this.pools = { a: 0, b: 0 };
        this.currentElixir = 0; // local side cache for UI
        this.side = 'a';
        this.maxElixir = 10;
        this.gameStart = false;
        this.elixirInterval = null;
        this.onChange = null;
    }

    setSide(side) {
        if (side === 'a' || side === 'b') {
            this.side = side;
        } else {
            this.side = 'spectate';
        }
        this.currentElixir = this.getElixir(this.side);
        this.updateElixirDisplay();
        this.updateElixirBar();
    }

    getElixir(side = this.side) {
        const key = side === 'b' ? 'b' : 'a';
        return this.pools[key] ?? 0;
    }

    setElixir(side, value, { emit = true } = {}) {
        const key = side === 'b' ? 'b' : 'a';
        const clamped = Math.max(0, Math.min(value, this.maxElixir));
        this.pools[key] = clamped;
        if (key === this.side) {
            this.currentElixir = clamped;
            this.updateElixirDisplay();
            this.updateElixirBar();
        }
        if (emit && typeof this.onChange === 'function') {
            this.onChange(key, clamped);
        }
        return clamped;
    }

    changeElixir(side, delta, opts = {}) {
        const next = this.getElixir(side) + delta;
        return this.setElixir(side, next, opts);
    }

    hasEnough(cost, side = this.side) {
        return this.getElixir(side) >= cost;
    }

    spend(cost, side = this.side, opts = {}) {
        if (typeof window !== 'undefined' && window.IS_HOST !== true) return false;
        if (!this.hasEnough(cost, side)) return false;
        this.changeElixir(side, -cost, opts);
        this.startElixirGeneration();
        return true;
    }

    // Start the elixir generation
    startElixirGeneration() {
        if (this.elixirInterval) return; // Already running
        if (typeof window !== 'undefined' && window.IS_HOST !== true) {
            console.log('[elixir] Client not host; skipping generation loop');
            return;
        }

        this.gameStart = true;
        console.log('Game started! Elixir generation begins...');

        // Generate +1 elixir per second
        this.elixirInterval = setInterval(() => {
            if (typeof window !== 'undefined' && window.IS_HOST !== true) return;
            let anyChanged = false;
            ['a', 'b'].forEach((side) => {
                if (this.getElixir(side) < this.maxElixir) {
                    anyChanged = true;
                    const next = this.getElixir(side) + 1;
                    this.setElixir(side, next);
                    console.log(`[elixir] ${side} -> ${next}/${this.maxElixir}`);
                }
            });
            if (!anyChanged) {
                this.stopElixirGeneration();
            }
        }, 1000); // 1 second interval
    }

    // Stop the elixir generation
    stopElixirGeneration() {
        if (this.elixirInterval) {
            clearInterval(this.elixirInterval);
            this.elixirInterval = null;
            console.log('Elixir generation stopped (max reached).');
        }
    }

    // Update the elixir count display
    updateElixirDisplay() {
        const elixirValueElement = document.getElementById('elixer-value');
        if (elixirValueElement) {
            elixirValueElement.textContent = this.currentElixir;
        }
    }

    // Update the elixir bar visual
    updateElixirBar() {
        const segments = document.querySelectorAll('.elixer-segment');

        // Fill segments from bottom to top with vivid violet color
        segments.forEach((segment, index) => {
            // Segments are ordered top to bottom, so we fill from the end
            const segmentIndex = segments.length - 1 - index;

            if (segmentIndex < this.currentElixir) {
                segment.style.backgroundColor = '#8B5CF6'; // Vivid violet
            } else {
                segment.style.backgroundColor = 'transparent';
            }
        });
    }

    // Reset elixir
    reset() {
        this.pools = { a: 0, b: 0 };
        this.currentElixir = 0;
        this.gameStart = false;
        this.stopElixirGeneration();
        this.updateElixirDisplay();
        this.updateElixirBar();
    }
}

// Create global elixir manager instance (idempotent if already present)
if (!window.elixirManager || !(window.elixirManager instanceof ElixirManager)) {
    window.elixirManager = new ElixirManager();
}
const elixirManager = window.elixirManager;
