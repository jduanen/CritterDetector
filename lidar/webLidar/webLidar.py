#!/usr/bin/env python3

import dash_bootstrap_components as dbc
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import plotly.graph_objs as go
from shapely import union_all
from shapely.geometry import Polygon, MultiPolygon
import numpy as np

import lidar


EPSILON = 0.0000001
MAX_MARGIN = 0.5
MIN_MARGIN = -0.5

coords = [[-4,-4], [4,-4], [4,4], [-4,4]]
poly = Polygon(coords)
xy = poly.exterior.coords
xSamples, ySamples = zip(*xy)

minRange = lidar.MIN_RANGE
maxRange = lidar.MAX_RANGE
minAngle = lidar.MIN_ANGLE
maxAngle = lidar.MAX_ANGLE
lastRanges = [minRange, maxRange]
lastAngles = [minAngle, maxAngle]
maxMargin = MAX_MARGIN
minMargin = MIN_MARGIN


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

#### TODO
####  * pushbutton and int [0-1000] (# scans)
####  * margin [<epsilion>-<maxRange>] (meters)
####  * real-time scans on/off button, or just outside range
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
                    id="integrateFrames",
                    children="Number of Frames",
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
                dbc.Label("Margins", align="center"),
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
                dbc.Col(dcc.Graph(id="samplePoints"), md=8),
                dbc.Col(controls, md=4)
            ],
            align="center",
        ),
    ],
    fluid=True,
)

@app.callback(
    Output("samplePoints", "figure"),
    Input("lidarRanges", "value"),
    Input("lidarAngles", "value"),
)
def update(ranges, angles):
    global lastRanges, lastAngles

    if ranges and (ranges != lastRanges):
        print(f"minR: {ranges[0]}, maxR: {ranges[1]}")
        lastRanges = ranges
    if angles and (angles != lastAngles):
        print(f"minA: {angles[0]}, maxA: {angles[1]}")
        lastAngles = angles

    fig = go.Figure(
        data=[
            go.Scatter(
                x=xSamples,
                y=ySamples,
                mode="markers",
                marker={"size": 8},
                fill="toself"
            )
        ],
        layout={
#            "xaxis": {"title": "X"},
#            "yaxis": {"title": "Y"},
            "xaxis_range": [-ranges[1], ranges[1]],
            "yaxis_range": [-ranges[1], ranges[1]]
        }
    )
    return fig


if __name__ == '__main__':
    app.run_server(debug=True, port=8050)

'''
vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
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
#### TODO make checklist for: margins, current samples, intensity?

options = [{"label": specie.capitalize(), "value": specie} for specie in species]

app = Dash(__name__)

app.layout = html.Div(
    [
        dcc.Checklist(
            options=options,
            inline=True,
            value=species,
            id="checklist",
        ),
        dcc.Graph(id="scatter"),
    ]
)


@app.callback(
    Output("scatter", "figure"),
    Input("checklist", "value"),
)
def update_figure(values):

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
#### TODO pushbutton for integrating new area (with given number of frames)

countdown_input = dcc.Input(
    id="countdown-input",
    type="number",
    min=0,
    step=1,
    size="lg",
    style={"font-size": "1.6rem"},
    className="mb-3",
)

button = dbc.Button(
    id="countdown-button",
    children="Start Countdown",
    n_clicks=0,
    size="lg",
    style={"font-size": "1.6rem"},
    color="primary",
    className="me-1",
)

app.layout = dbc.Container(
    [
        countdown_store,
        running_countdown_store,
        interval,
        audio_div,
        dbc.Row(
            [
                dbc.Col(
                    [html.H2("Enter countdown in seconds"), countdown_input, button],
                    lg=6,
                )
            ],
            justify="center",
            style=dict(textAlign="center"),
            className="d-flex justify-content-center",
        ),

@app.callback(
    Output("countdown-store", "data"),
    Output("countdown-interval", "n_intervals"),
    Input("countdown-button", "n_clicks"),
    State("countdown-input", "value"),
)
def init_countdown_store(n_clicks, countdown_input):

    if n_clicks > 0:

        return countdown_input, 0

@app.callback(
    Output("running-countdown-store", "data"),
    Input("countdown-store", "data"),
    Input("countdown-interval", "n_intervals"),
)
def init_running_countdown_store(seconds, n_intervals):

    if seconds is not None:

        running_seconds = seconds - n_intervals
        if running_seconds >= 0:
            return running_seconds
        else:
            return


---------
#### TODO consider using dcc.Interval to run scans of lidar device

interval = dcc.Interval(
    id="countdown-interval", interval=1000, n_intervals=0
)

use dcc.Store to save state between calls

---------
#### TODO make hover mouse show (distance, intensity) for sample points



---------
#### TODO 
'''