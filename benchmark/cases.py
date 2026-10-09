import plotly.graph_objects as go

CHARTS = {
    # 1. Core Cartesian
    'scatter_line': {
        'category': 'Core Cartesian',
        'title': 'Scatter & Line Chart',
        'fig': go.Figure(
            data=[
                go.Scatter(x=[1, 2, 3, 4, 5, 6], y=[10, 15, 13, 17, 22, 19], mode='lines+markers', name='Series A'),
                go.Scatter(x=[1, 2, 3, 4, 5, 6], y=[16, 11, 9, 14, 18, 25], mode='lines+markers', name='Series B'),
            ],
            layout=go.Layout(title='Scatter & Line Chart', width=650, height=450),
        ),
    },
    'bar': {
        'category': 'Core Cartesian',
        'title': 'Grouped Bar Chart',
        'fig': go.Figure(
            data=[
                go.Bar(name='2025', x=['Product A', 'Product B', 'Product C', 'Product D'], y=[32, 58, 44, 76]),
                go.Bar(name='2026', x=['Product A', 'Product B', 'Product C', 'Product D'], y=[45, 67, 52, 89]),
            ],
            layout=go.Layout(title='Grouped Bar Chart', barmode='group', width=650, height=450),
        ),
    },
    'pie': {
        'category': 'Core Cartesian',
        'title': 'Donut / Pie Chart',
        'fig': go.Figure(
            data=[
                go.Pie(
                    labels=['Direct', 'Organic Search', 'Paid Referral', 'Social', 'Email'],
                    values=[35, 25, 20, 12, 8],
                    hole=0.3,
                )
            ],
            layout=go.Layout(title='Traffic Distribution (Donut)', width=650, height=450),
        ),
    },
    'box': {
        'category': 'Core Cartesian',
        'title': 'Box Plot',
        'fig': go.Figure(
            data=[
                go.Box(y=[12, 15, 18, 19, 21, 22, 24, 25, 29, 31, 35], name='Control'),
                go.Box(y=[18, 22, 24, 27, 28, 30, 33, 36, 40, 42, 45], name='Treatment'),
            ],
            layout=go.Layout(title='Box Plot Distribution', width=650, height=450),
        ),
    },
    'violin': {
        'category': 'Core Cartesian',
        'title': 'Violin Plot',
        'fig': go.Figure(
            data=[
                go.Violin(
                    y=[10, 12, 14, 15, 16, 18, 19, 20, 22, 25, 29, 32],
                    box_visible=True,
                    meanline_visible=True,
                    name='Alpha',
                ),
                go.Violin(
                    y=[16, 18, 20, 21, 22, 24, 25, 26, 28, 30, 35, 38],
                    box_visible=True,
                    meanline_visible=True,
                    name='Beta',
                ),
            ],
            layout=go.Layout(title='Violin Distribution Plot', width=650, height=450),
        ),
    },
    'histogram': {
        'category': 'Core Cartesian',
        'title': 'Frequency Histogram',
        'fig': go.Figure(
            data=[
                go.Histogram(
                    x=[1.2, 1.5, 1.8, 2.0, 2.1, 2.2, 2.5, 2.7, 2.9, 3.0, 3.1, 3.2, 3.5, 3.8, 4.0, 4.2, 4.5, 4.8, 5.0],
                    nbinsx=8,
                    name='Sample Set',
                )
            ],
            layout=go.Layout(title='Frequency Histogram', width=650, height=450),
        ),
    },
    'histogram2d': {
        'category': 'Core Cartesian',
        'title': '2D Density Histogram',
        'fig': go.Figure(
            data=[
                go.Histogram2d(x=[1, 1, 2, 2, 2, 3, 3, 3, 3, 4], y=[1, 2, 2, 3, 3, 3, 4, 4, 4, 5], nbinsx=6, nbinsy=6)
            ],
            layout=go.Layout(title='2D Density Histogram', width=650, height=450),
        ),
    },
    'contour': {
        'category': 'Core Cartesian',
        'title': '2D Contour Plot',
        'fig': go.Figure(
            data=[
                go.Contour(
                    z=[
                        [10, 10.6, 12.3, 14.0],
                        [10.6, 12.5, 14.5, 16.2],
                        [12.3, 14.5, 17.1, 19.3],
                        [14.0, 16.2, 19.3, 22.0],
                    ],
                    colorscale='Blues',
                )
            ],
            layout=go.Layout(title='2D Contour Plot', width=650, height=450),
        ),
    },
    'heatmap': {
        'category': 'Core Cartesian',
        'title': 'Performance Heatmap',
        'fig': go.Figure(
            data=[
                go.Heatmap(
                    z=[[10, 25, 30, 45], [20, 35, 55, 65], [30, 45, 70, 85], [40, 60, 80, 95]],
                    x=['Q1', 'Q2', 'Q3', 'Q4'],
                    y=['North', 'South', 'East', 'West'],
                    colorscale='Viridis',
                )
            ],
            layout=go.Layout(title='Performance Heatmap', width=650, height=450),
        ),
    },
    'scatterternary': {
        'category': 'Core Cartesian',
        'title': 'Ternary Phase Diagram',
        'fig': go.Figure(
            data=[
                go.Scatterternary(a=[40, 30, 20], b=[30, 50, 60], c=[30, 20, 20], mode='lines+markers', name='Phase')
            ],
            layout=go.Layout(title='Ternary Phase Diagram', width=650, height=450),
        ),
    },
    # 2. Financial & Flow
    'candlestick': {
        'category': 'Financial & Business',
        'title': 'Candlestick Stock Chart',
        'fig': go.Figure(
            data=[
                go.Candlestick(
                    x=['2026-01-01', '2026-01-02', '2026-01-03', '2026-01-04', '2026-01-05'],
                    open=[100, 105, 103, 108, 107],
                    high=[108, 110, 109, 115, 112],
                    low=[98, 101, 99, 105, 102],
                    close=[105, 103, 108, 107, 111],
                )
            ],
            layout=go.Layout(title='Candlestick Stock Chart', width=650, height=450),
        ),
    },
    'ohlc': {
        'category': 'Financial & Business',
        'title': 'OHLC Financial Chart',
        'fig': go.Figure(
            data=[
                go.Ohlc(
                    x=['2026-01-01', '2026-01-02', '2026-01-03', '2026-01-04', '2026-01-05'],
                    open=[100, 105, 103, 108, 107],
                    high=[108, 110, 109, 115, 112],
                    low=[98, 101, 99, 105, 102],
                    close=[105, 103, 108, 107, 111],
                )
            ],
            layout=go.Layout(title='OHLC Financial Chart', width=650, height=450),
        ),
    },
    'waterfall': {
        'category': 'Financial & Business',
        'title': 'Waterfall Profit & Loss',
        'fig': go.Figure(
            data=[
                go.Waterfall(
                    name='2026',
                    orientation='v',
                    measure=['relative', 'relative', 'total', 'relative', 'total'],
                    x=['Sales', 'Consulting', 'Gross Revenue', 'Expenses', 'Net Profit'],
                    y=[60, 20, 0, -35, 0],
                    connector={'line': {'color': 'rgb(63, 63, 63)'}},
                )
            ],
            layout=go.Layout(title='Waterfall Profit & Loss', width=650, height=450),
        ),
    },
    'funnel': {
        'category': 'Financial & Business',
        'title': 'Sales Conversion Funnel',
        'fig': go.Figure(
            data=[go.Funnel(y=['Website Visit', 'Sign Up', 'Demo Request', 'Purchase'], x=[12000, 5500, 2100, 950])],
            layout=go.Layout(title='Sales Conversion Funnel', width=650, height=450),
        ),
    },
    'funnelarea': {
        'category': 'Financial & Business',
        'title': 'Funnel Area Analysis',
        'fig': go.Figure(
            data=[go.Funnelarea(values=[10000, 4500, 1800, 800], text=['Visitors', 'Leads', 'Proposals', 'Deals'])],
            layout=go.Layout(title='Funnel Area Analysis', width=650, height=450),
        ),
    },
    'indicator': {
        'category': 'Financial & Business',
        'title': 'KPI Performance Indicator',
        'fig': go.Figure(
            data=[
                go.Indicator(
                    mode='number+delta+gauge',
                    value=450,
                    delta={'reference': 400, 'relative': True},
                    gauge={'axis': {'range': [None, 500]}, 'bar': {'color': '#1f77b4'}},
                )
            ],
            layout=go.Layout(title='KPI Performance Indicator', width=650, height=450),
        ),
    },
    # 3. Hierarchical
    'treemap': {
        'category': 'Hierarchical',
        'title': 'Market Cap Treemap',
        'fig': go.Figure(
            data=[
                go.Treemap(
                    labels=['Market', 'Tech', 'Finance', 'Energy', 'Apple', 'Microsoft', 'JPMorgan', 'Chevron'],
                    parents=['', 'Market', 'Market', 'Market', 'Tech', 'Tech', 'Finance', 'Energy'],
                    values=[0, 0, 0, 0, 120, 110, 80, 70],
                )
            ],
            layout=go.Layout(title='Market Cap Treemap', width=650, height=450),
        ),
    },
    'sunburst': {
        'category': 'Hierarchical',
        'title': 'Global Sunburst Hierarchy',
        'fig': go.Figure(
            data=[
                go.Sunburst(
                    labels=['World', 'Europe', 'Asia', 'France', 'Germany', 'Japan', 'China'],
                    parents=['', 'World', 'World', 'Europe', 'Europe', 'Asia', 'Asia'],
                    values=[0, 0, 0, 65, 83, 125, 1400],
                )
            ],
            layout=go.Layout(title='Global Sunburst Hierarchy', width=650, height=450),
        ),
    },
    'icicle': {
        'category': 'Hierarchical',
        'title': 'Icicle Partition Chart',
        'fig': go.Figure(
            data=[
                go.Icicle(
                    labels=['Root', 'Cluster 1', 'Cluster 2', 'Sub A', 'Sub B', 'Sub C'],
                    parents=['', 'Root', 'Root', 'Cluster 1', 'Cluster 1', 'Cluster 2'],
                    values=[0, 0, 0, 10, 20, 35],
                )
            ],
            layout=go.Layout(title='Icicle Partition Chart', width=650, height=450),
        ),
    },
    # 4. Polar / Radial
    'scatterpolar': {
        'category': 'Radial & Polar',
        'title': 'Radar Performance Comparison',
        'fig': go.Figure(
            data=[
                go.Scatterpolar(
                    r=[80, 90, 70, 85, 95],
                    theta=['Speed', 'Power', 'Range', 'Defense', 'Agility'],
                    fill='toself',
                    name='Model X',
                ),
                go.Scatterpolar(
                    r=[65, 75, 90, 80, 70],
                    theta=['Speed', 'Power', 'Range', 'Defense', 'Agility'],
                    fill='toself',
                    name='Model Y',
                ),
            ],
            layout=go.Layout(title='Radar Performance Comparison', width=650, height=450),
        ),
    },
    'barpolar': {
        'category': 'Radial & Polar',
        'title': 'Polar Wind Rose',
        'fig': go.Figure(
            data=[
                go.Barpolar(
                    r=[3, 4.5, 2, 5, 6, 3, 2, 4], theta=['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'], name='Wind Force'
                )
            ],
            layout=go.Layout(title='Polar Wind Rose', width=650, height=450),
        ),
    },
    # 5. Specialized Diagrams & Tables
    'sankey': {
        'category': 'Specialized Diagrams',
        'title': 'Energy Flow Sankey Diagram',
        'fig': go.Figure(
            data=[
                go.Sankey(
                    node=dict(
                        pad=15,
                        thickness=20,
                        line=dict(color='black', width=0.5),
                        label=['Solar', 'Wind', 'Grid', 'Residential', 'Industry'],
                    ),
                    link=dict(source=[0, 1, 0, 2, 2], target=[2, 2, 3, 3, 4], value=[8, 6, 2, 9, 7]),
                )
            ],
            layout=go.Layout(title='Energy Flow Sankey Diagram', width=650, height=450),
        ),
    },
    'parcats': {
        'category': 'Specialized Diagrams',
        'title': 'Parallel Categories Diagram',
        'fig': go.Figure(
            data=[
                go.Parcats(
                    dimensions=[
                        dict(label='Hair', values=['Fair', 'Brown', 'Brown', 'Brown', 'Fair']),
                        dict(label='Eye', values=['Blue', 'Brown', 'Hazel', 'Blue', 'Green']),
                        dict(label='Sex', values=['Female', 'Male', 'Female', 'Male', 'Female']),
                    ]
                )
            ],
            layout=go.Layout(title='Parallel Categories Diagram', width=650, height=450),
        ),
    },
    'table': {
        'category': 'Specialized Diagrams',
        'title': 'Formatted Data Table',
        'fig': go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=['Item ID', 'Category', 'Unit Price', 'Stock Level'],
                        fill_color='paleturquoise',
                        align='left',
                    ),
                    cells=dict(
                        values=[
                            [101, 102, 103, 104],
                            ['Hardware', 'Software', 'Service', 'Hardware'],
                            ['$499', '$120', '$85', '$250'],
                            [45, 120, 800, 12],
                        ],
                        fill_color='lavender',
                        align='left',
                    ),
                )
            ],
            layout=go.Layout(title='Formatted Inventory Table', width=650, height=450),
        ),
    },
    'carpet': {
        'category': 'Specialized Diagrams',
        'title': 'Carpet Coordinate Plot',
        'fig': go.Figure(
            data=[
                go.Carpet(
                    a=[4, 4.5, 5],
                    b=[1, 2, 3],
                    y=[[2, 3.5, 4], [3, 4.5, 5], [5, 5.5, 7]],
                    aaxis=dict(tickprefix='a = ', smoothing=0, minorgridcount=9),
                    baxis=dict(tickprefix='b = ', smoothing=0, minorgridcount=9),
                ),
                go.Scattercarpet(
                    a=[4, 4.5, 5], b=[1.5, 2.5, 1.5], line=dict(shape='spline', smoothing=1, color='crimson')
                ),
            ],
            layout=go.Layout(title='Carpet Coordinate Plot', width=650, height=450),
        ),
    },
    'rotated_ticks_45': {
        'category': 'Layout edge cases',
        'title': 'Bar chart with X labels at 45 deg',
        'fig': go.Figure(
            data=[go.Bar(x=['Category A', 'Category B', 'Category C', 'Category D'], y=[1, 2, 3, 4])],
            layout=go.Layout(
                template='plotly',
                width=500,
                height=400,
                title='Tickangle 45',
                xaxis=dict(tickangle=45, title='X Axis Title', automargin=True),
                yaxis=dict(title='Y'),
            ),
        ),
    },
    'rotated_ticks_90': {
        'category': 'Layout edge cases',
        'title': 'Bar chart with X labels at 90 deg',
        'fig': go.Figure(
            data=[go.Bar(x=['Category A', 'Category B', 'Category C', 'Category D'], y=[1, 2, 3, 4])],
            layout=go.Layout(
                template='plotly',
                width=500,
                height=400,
                title='Tickangle 90',
                xaxis=dict(tickangle=90, title='X Axis Title', automargin=True),
                yaxis=dict(title='Y'),
            ),
        ),
    },
}
