/**
 * GM Axis Visualization Library
 * Creates horizontal axis charts showing player position relative to GMs
 */

class GMAxisViz {
  constructor() {
    this.visualizations = [];
  }

  /**
   * Create an axis visualization
   * @param {string} containerId - ID of the container element
   * @param {Object} config - Configuration object
   *   - min: minimum value for the axis
   *   - max: maximum value for the axis
   *   - player: { name, value }
   *   - gms: [{ name, value }, ...]
   */
  create(containerId, config) {
    const container = document.getElementById(containerId);
    if (!container) {
      console.warn(`Container ${containerId} not found`);
      return;
    }

    const { min, max, player, gms } = config;
    const range = max - min;

    // Clear existing content
    container.innerHTML = '';

    // Create GM markers
    if (gms && gms.length > 0) {
      gms.forEach(gm => {
        const percentage = this.calculatePercentage(gm.value, min, range);
        const marker = this.createMarker(gm.name, gm.value, percentage, false);
        container.appendChild(marker);
      });
    }

    // Create player marker
    if (player) {
      const playerPercentage = this.calculatePercentage(player.value, min, range);
      const playerMarker = this.createMarker(player.name, player.value, playerPercentage, true);
      container.appendChild(playerMarker);
    }

    this.visualizations.push({ containerId, config });
  }

  calculatePercentage(value, min, range) {
    if (range === 0) return 50; // Default to center if no range
    const percentage = ((value - min) / range) * 100;
    // Clamp between 2% and 98% to prevent edge overflow
    return Math.max(2, Math.min(98, percentage));
  }

  createMarker(name, value, percentage, isPlayer) {
    const marker = document.createElement('div');
    marker.className = isPlayer ? 'player-marker' : 'gm-marker';
    marker.style.left = `${percentage}%`;

    const label = document.createElement('div');
    label.className = isPlayer ? 'player-marker-label' : 'gm-marker-label';
    label.textContent = name;

    const dot = document.createElement('div');
    dot.className = isPlayer ? 'player-marker-dot' : 'gm-marker-dot';

    const line = document.createElement('div');
    line.className = isPlayer ? 'player-marker-line' : 'gm-marker-line';

    const valueLabel = document.createElement('div');
    valueLabel.className = isPlayer ? 'player-marker-value' : 'gm-marker-value';
    valueLabel.textContent = this.formatValue(value);

    marker.appendChild(label);
    marker.appendChild(dot);
    marker.appendChild(line);
    marker.appendChild(valueLabel);

    return marker;
  }

  formatValue(value) {
    if (typeof value === 'number') {
      const fixed = value.toFixed(1);
      return value % 1 === 0 ? `${Math.round(value)}%` : `${fixed}%`;
    }
    return value;
  }

  /**
   * Batch create multiple visualizations
   * @param {Object} configs - Object with containerId as key and config as value
   */
  createMultiple(configs) {
    Object.keys(configs).forEach(containerId => {
      this.create(containerId, configs[containerId]);
    });
  }

  /**
   * Update an existing visualization
   * @param {string} containerId - ID of the container element
   * @param {Object} newConfig - New configuration
   */
  update(containerId, newConfig) {
    const index = this.visualizations.findIndex(v => v.containerId === containerId);
    if (index !== -1) {
      this.visualizations[index].config = newConfig;
      this.create(containerId, newConfig);
    }
  }

  /**
   * Remove all visualizations
   */
  clear() {
    this.visualizations.forEach(viz => {
      const container = document.getElementById(viz.containerId);
      if (container) {
        container.innerHTML = '';
      }
    });
    this.visualizations = [];
  }
}

// Export as global
window.GMAxisViz = GMAxisViz;

// Helper function for quick access
window.createGMAxis = function(containerId, config) {
  if (!window.gmAxisVizInstance) {
    window.gmAxisVizInstance = new GMAxisViz();
  }
  window.gmAxisVizInstance.create(containerId, config);
};
