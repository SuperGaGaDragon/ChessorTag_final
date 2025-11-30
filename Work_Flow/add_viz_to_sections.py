#!/usr/bin/env python3
"""
Script to add GM axis visualizations to sections 2.2-2.8
"""

# Sections that need visualizations
sections_config = [
    {
        'id': 'style-prophylaxis',
        'viz_id': 'viz-prophylaxis-axis',
        'title': 'Overall Prophylaxis Ratio vs Top GMs',
        'scale': ['0%', '10%', '20%', '30%', '40%']
    },
    {
        'id': 'style-semantic_control',
        'viz_id': 'viz-semantic-control-axis',
        'title': 'Semantic Control Ratio vs Top GMs',
        'scale': ['0%', '15%', '30%', '45%', '60%']
    },
    {
        'id': 'style-control_over_dynamics',
        'viz_id': 'viz-cod-axis',
        'title': 'Control Over Dynamics vs Top GMs',
        'scale': ['0%', '15%', '30%', '45%', '60%']
    },
    {
        'id': 'style-initiative',
        'viz_id': 'viz-initiative-axis',
        'title': 'Initiative Attempt Ratio vs Top GMs',
        'scale': ['0%', '10%', '20%', '30%', '40%']
    },
    {
        'id': 'style-tension',
        'viz_id': 'viz-tension-axis',
        'title': 'Tension Creation Ratio vs Top GMs',
        'scale': ['0%', '5%', '10%', '15%', '20%']
    },
    {
        'id': 'style-structural',
        'viz_id': 'viz-structural-axis',
        'title': 'Structural Integrity Ratio vs Top GMs',
        'scale': ['0%', '20%', '40%', '60%', '80%']
    },
    {
        'id': 'style-sacrifice',
        'viz_id': 'viz-sacrifice-axis',
        'title': 'Overall Sacrifice Ratio vs Top GMs',
        'scale': ['0%', '3%', '6%', '9%', '12%']
    }
]

def generate_viz_html(config):
    """Generate visualization HTML for a section"""
    scales = ''.join([f'<span class="gm-scale-mark">{s}</span>\n                    ' for s in config['scale']])

    return f'''
                <!-- GM Comparison Axis Visualization -->
                <div class="gm-axis-viz">
                  <div class="gm-axis-title">{config['title']}</div>
                  <div class="gm-axis-container">
                    <div class="gm-axis-line"></div>
                    <div class="gm-markers-layer" id="{config['viz_id']}"></div>
                  </div>
                  <div class="gm-axis-scale">
                    {scales.strip()}
                  </div>
                  <div class="gm-axis-legend">
                    <div class="legend-item">
                      <div class="legend-dot"></div>
                      <span>Top GMs</span>
                    </div>
                    <div class="legend-item">
                      <div class="legend-dot player"></div>
                      <span>You</span>
                    </div>
                  </div>
                </div>
'''

print("Generated visualization HTML snippets:")
print("=" * 60)
for config in sections_config:
    print(f"\n<!-- For section {config['id']} -->")
    print(generate_viz_html(config))
