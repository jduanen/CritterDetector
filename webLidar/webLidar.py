#!/usr/bin/env python3
#
# N.B. Dash is multi-threaded, need to use dcc.Store() objects instead of globals
#


import dash_bootstrap_components as dbc
from dash import Dash, html, dash_table, dcc, callback, ctx, Input, Output, State
import dash_daq as daq
import plotly.graph_objs as go
from shapely import union_all
from shapely.geometry import Polygon, MultiPolygon
import numpy as np

import lidar


EPSILON = 0.0000001
MAX_MARGIN = 0.5
MIN_MARGIN = -0.5

OPTS_SAMPLE = 0
OPTS_MARGIN = 1
OPTS_OUTSIDE = 2
OPTS_REGION = 3

minRange = lidar.MIN_RANGE
maxRange = lidar.MAX_RANGE
minAngle = lidar.MIN_ANGLE
maxAngle = lidar.MAX_ANGLE
lastRanges = [minRange, maxRange]
lastAngles = [minAngle, maxAngle]
maxMargin = MAX_MARGIN
minMargin = MIN_MARGIN

#### TMP TMP TMP
coords = [[0,1], [0.5,-1], [-0.5,-1], [0,1]]
poly = Polygon(coords)
xy = poly.exterior.coords
xSamples, ySamples = zip(*xy)

scanner = None

isLaserOn = False

#fig = go.Figure()

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

controls = dbc.Card(
    [
        html.H5("Scan Region"),
        html.Div(
            [
                dbc.Label("Ranges", align="center"),
                #### TODO consider setting 'updatemode="drag"'
                dcc.RangeSlider(
                    id="lidarRanges",
                    min=lidar.MIN_RANGE,
                    max=lidar.MAX_RANGE,
                    step=0.01,
                    count=2,
                    pushable=0.02,
                    value=[minRange, maxRange],
                    marks={v: f"{float(v)}" for v in range(int(lidar.MAX_RANGE))},
                    allowCross=False,
                    drag_value=None,
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ]
        ),
        html.Div(
            [
                dbc.Label("Angles", align="center"),
                dcc.RangeSlider(
                    id="lidarAngles",
                    min=lidar.MIN_ANGLE,
                    max=lidar.MAX_ANGLE,
                    step=0.25,
                    count=2,
                    pushable=0.05,
                    value=[minAngle, maxAngle],
                    marks={-180.0: str(-180.0), 0.0: "0.0", 180.0: str(180)},
                    allowCross=False,
                    drag_value=None,
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ]
        ),
        html.Hr(),
        html.H5("Reference Region"),
        html.Div(
            [
                dbc.Label("Margins", align="center"),
                #### TODO consider setting 'updatemode="drag"'
                dcc.RangeSlider(
                    id="lidarMargins",
                    min=MIN_MARGIN,
                    max=MAX_MARGIN,
                    step=0.01,
                    count=2,
                    pushable=0.01,
                    value=[minMargin, maxMargin],
                    marks={minMargin: f"{minMargin}", 0.0: "0.0", maxMargin: f"{maxMargin}"},
                    allowCross=False,
                    drag_value=None,
                    tooltip={"placement": "bottom", "always_visible": True}
                )
            ]
        ),
        html.Div(
            [
                dbc.Button(
                    id="intersectFrames",
                    children="Intersect Frames",
                    n_clicks=0,
                    size="sm",
                    #style={"font-size": "1.6rem"},
                    color="primary",
                    className="me-1",
                ),
                dcc.Input(
                    id="numFrames",
                    type="number",
                    min=0,
                    max=1000,
                    step=1,
                    value=50,
                    size="sm",
                    #style={"font-size": "1.6rem"},
                    className="mb-3",
                ),
            ]
        ),
        html.Hr(),
        html.H5("Display Options"),
        html.Div(
            [
                dcc.Checklist(
                    options=[
                        {"label": "samples", "value": OPTS_SAMPLE},
                        {"label": "margins", "value": OPTS_MARGIN},
                        {"label": "outside", "value": OPTS_OUTSIDE},
                        {"label": "region", "value": OPTS_REGION},
                    ],
                    inline=True,
                    value=[],
                    inputStyle={"margin-right": "5px"},
                    labelStyle={"margin-right": "20px"},
                    id="displayOptions",
                ),
            ]
        ),
        html.Div(
            [
                dcc.Checklist(
                    options=[ {"label": "Sample Intensity Enable", "value": 0} ],
                    inline=True,
                    value=[],
                    inputStyle={"margin-right": "5px"},
                    labelStyle={"margin-right": "20px"},
                    id="intensityEnb",
                ),
            ],
        ),
    ],
    body=True,
)

app.layout = dbc.Container(
    [
        html.H1("Lidar Scan"),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(id="lidarDisplay",
                        figure=go.Figure(),
                        responsive=True,
                        style={'width': '90vh', 'height': '90vh'}
                    )
                ),
            ],
            align="center",
            className='g-0',
        ),
        dbc.Row(
            [
                dbc.Col(controls),
            ],
            align="center",
            className='g-0',
        ),
    ],
    fluid=True,
)


def getSamples():
    if not scanner:
        print("NO SAMPLES")
        return None, None  ##xSamples = ySamples = [(0, 0)]

    angles, distances, intensity = scanner.scanIntensity()
    polarToCartesian = lambda theta, r: ((r * np.cos(theta)), (r * np.sin(theta)))
    cartCoords = [polarToCartesian(theta, r) for theta, r in zip(angles, distances)]
    poly = Polygon(cartCoords)
    xy = poly.exterior.coords
    xSamples, ySamples = zip(*xy)
    print(f"SSSSSS: {len(xSamples)}")

    fig = go.Figure(
        data=[
            go.Scatter(
                x=xSamples,
                y=ySamples,
                mode="markers",
                #marker={"size": 8},
                fill="toself"
            )
        ],
        layout={
            "xaxis": {"scaleanchor": "y", "scaleratio": 1, "constrain": "range"},
            "yaxis": {"scaleanchor": "x", "scaleratio": 1, "constrain": "range"},
            "xaxis_range": [-lastRanges[1], lastRanges[1]],
            "yaxis_range": [-lastRanges[1], lastRanges[1]],
        }
    )
    return fig

@app.callback(
    Output("lidarDisplay", "figure"),
    Input("lidarRanges", "value"),
    Input("lidarAngles", "value"),
    Input("lidarMargins", "value"),
    Input("intersectFrames", "n_clicks"),
    Input("displayOptions", "value"),
    Input("intensityEnb", "value"),
    State("numFrames", "value"),
)
def update(ranges, angles, margins, intersect, options, intensityEnb, numFrames):
    global lastRanges, lastAngles, scanner

    if options:
        scanner = lidar.Lidar(zeroFilter=True)
    else:
        scanner = None

    if ranges and (ranges != lastRanges):
        print(f"minR: {ranges[0]}, maxR: {ranges[1]}")
        lastRanges = ranges
        if scanner:
            scanner.setRanges(ranges[0], ranges[1])
            print(f"RRRRRR: {scanner.getRanges()[0]}, {scanner.getRanges()[1]}")

    if angles and (angles != lastAngles):
        print(f"minA: {angles[0]}, maxA: {angles[1]}")
        lastAngles = angles
        if scanner:
            scanner.setAngles(angles[0], angles[1])
            print(f"AAAAAA: {scanner.getAngles()[0]}, {scanner.getAngles()[1]}")

    print(f"margins: {margins}")
    print(f"intersect: {intersect}, numFrames: {numFrames}")

    print(f"displayOptions: {options}")
    fig = None
    if OPTS_SAMPLE in options:
        print("SAMPLE")
        print(f"intensityEnb: {intensityEnb}")
        fig = getSamples()
    elif OPTS_MARGIN in options:
        print("MARGIN")
    elif OPTS_REGION in options:
        print("REGION")
    elif OPTS_OUTSIDE in options:
        print("OUTSIDE")

    return fig if fig else go.Figure()


if __name__ == '__main__':
    app.run_server(debug=True, port=8050)

    #### FIXME this won't work
#    if scanner:
#        scanner.done()

'''
vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
#### TODO think about adding simplify and tolerance button and input box

#### TODO make a small bitmap/icon of a triangle pointing up, corresponding to the mark on the lidar device top

---------
#### TODO make each sample point a color proportional to its intensity

colorscales = px.colors.named_colorscales()

app.layout = html.Div(
    [
        html.H4("Interactive Plotly Express color scale selection"),
        html.P("Color Scale"),
        dcc.Dropdown(
            id="dropdown", options=colorscales, value="viridis"
        ),
        dcc.Graph(id="graph"),
    ]
)

@app.callback(
    Output("graph", "figure"),
    Input("dropdown", "value"),
)
def change_colorscale(scale):
    fig = px.scatter(
        df,
        x="sepal_width",
        y="sepal_length",
        color="sepal_length",
        color_continuous_scale=scale,
    )
    return fig

--------
#### TODO add boolean switch for dark/light theme

template="plotly_dark",

app.layout = html.Div(
    [
        html.H2("Colour by Type BooleanSwitch Example App"),
        html.P("colour off | colour on", style={"textAlign": "center"}),
        daq.BooleanSwitch(id="pb", on=False),
        html.Div(id="pb-result")
    ]
)

@app.callback(
    Output("pb-result", "children"),
    Input("pb", "on"),
)
def update_output(on):

---------
#### TODO common or independent callback handlers???? 

@app.callback(
    Output("meter", "value"),
    Output("feet", "value"),
    Output("map", "figure"),
    Input("meter", "value"),
    Input("feet", "value"),
)
def sync_input(meter, feet):
    if ctx.triggered_id == "meter":
        feet = None if meter is None else round((float(meter) * 3.28084), 0)
    else:
        meter = None if feet is None else round((float(feet) / 3.28084), 1)

    fig = px.scatter_geo(
        data_frame=df.loc[df["Elev"] >= meter],
        lat="Latitude",
        lon="Longitude",
        size="Elev",
        hover_name="Volcano Name",
        projection="natural earth",
    )

    return meter, feet, fig

---------
#### TODO consider using dcc.Interval to run scans of lidar device

interval = dcc.Interval(
    id="countdown-interval", interval=1000, n_intervals=0
)

use dcc.Store to save state between calls

---------
#### TODO 
'''