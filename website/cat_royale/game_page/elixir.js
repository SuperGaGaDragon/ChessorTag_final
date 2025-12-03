// Elixir Management System
class ElixirManager {
    constructor() {
        this.currentElixir = 0;
        this.maxElixir = 10;
        this.gameStart = false;
        this.elixirInterval = null;
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
            if (this.currentElixir < this.maxElixir) {
                this.currentElixir++;
                this.updateElixirDisplay();
                this.updateElixirBar();
                console.log(`Elixir: ${this.currentElixir}/${this.maxElixir}`);
                if (typeof window !== 'undefined' && window.IS_HOST === true && typeof window.postToParent === 'function') {
                    window.postToParent('state_update', {
                        type: 'state_update',
                        event: 'elixir',
                        side: 'a',
                        elixir: this.currentElixir
                    });
                }

                if (this.currentElixir >= this.maxElixir) {
                    this.stopElixirGeneration();
                }
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
        this.currentElixir = 0;
        this.gameStart = false;
        this.stopElixirGeneration();
        this.updateElixirDisplay();
        this.updateElixirBar();
    }
}

// Create global elixir manager instance
const elixirManager = new ElixirManager();
