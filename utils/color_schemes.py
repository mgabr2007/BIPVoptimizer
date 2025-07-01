"""
Yellow Color Scheme for BIPV Optimizer
Provides consistent color palettes throughout the application
"""

# Primary yellow color scheme
YELLOW_SCHEME = {
    'primary': '#FFD700',           # Gold
    'secondary': '#FFA500',         # Orange
    'accent': '#FFFF00',            # Yellow
    'light': '#FFFACD',             # Lemon Chiffon
    'dark': '#DAA520',              # Goldenrod
    'warning': '#FF8C00',           # Dark Orange
    'success': '#9ACD32',           # Yellow Green
    'info': '#FFE4B5',              # Moccasin
    'background': '#FFFEF7',        # Cream White
    'secondary_bg': '#FFF8DC',      # Cornsilk
    'text': '#2F2F2F'               # Dark Gray
}

# Chart color palettes
CHART_COLORS = {
    'single': YELLOW_SCHEME['primary'],
    'gradient': ['#FFD700', '#FFA500', '#FF8C00', '#DAA520', '#B8860B'],
    'categorical': [
        '#FFD700',  # Gold
        '#FFA500',  # Orange  
        '#FF8C00',  # Dark Orange
        '#DAA520',  # Goldenrod
        '#B8860B',  # Dark Goldenrod
        '#F0E68C',  # Khaki
        '#FFFF00',  # Yellow
        '#9ACD32'   # Yellow Green
    ],
    'heatmap': ['#FFFACD', '#FFD700', '#FFA500', '#FF8C00', '#DAA520'],
    'diverging': ['#B8860B', '#DAA520', '#FFD700', '#FFA500', '#FF8C00']
}

# Status colors
STATUS_COLORS = {
    'completed': YELLOW_SCHEME['success'],
    'current': YELLOW_SCHEME['primary'],
    'pending': YELLOW_SCHEME['light'],
    'error': YELLOW_SCHEME['warning'],
    'info': YELLOW_SCHEME['info']
}

def get_plotly_template():
    """Get Plotly template with yellow color scheme"""
    return {
        'layout': {
            'colorway': CHART_COLORS['categorical'],
            'paper_bgcolor': YELLOW_SCHEME['background'],
            'plot_bgcolor': YELLOW_SCHEME['secondary_bg'],
            'font': {'color': YELLOW_SCHEME['text']},
            'colorscale': {
                'sequential': [
                    [0, YELLOW_SCHEME['light']],
                    [0.5, YELLOW_SCHEME['primary']],
                    [1, YELLOW_SCHEME['dark']]
                ]
            }
        }
    }

def get_chart_color(index=0):
    """Get chart color by index for consistent coloring"""
    colors = CHART_COLORS['categorical']
    return colors[index % len(colors)]

def get_gradient_colors(n_colors=5):
    """Get gradient colors for heatmaps and continuous scales"""
    if n_colors <= len(CHART_COLORS['gradient']):
        return CHART_COLORS['gradient'][:n_colors]
    
    # Generate interpolated colors if more needed
    base_colors = CHART_COLORS['gradient']
    step = len(base_colors) / n_colors
    return [base_colors[int(i * step)] for i in range(n_colors)]