#!/usr/bin/env python3

import dash_bootstrap_components as dbc
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import plotly.graph_objs as go
from shapely import union_all
from shapely.geometry import Polygon, MultiPolygon
import numpy as np

import lidar


coords = [[0,0], [5,0], [5,5], [0,5]]
poly = Polygon(coords)
xy = poly.exterior.coords
xSamples, ySamples = zip(*xy)

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

#### TODO
####  * pushbutton and int [0-1000] (# scans)
####  * minRange and maxRange sliders [0-16] (meters)
####  * minAngle and maxAngle sliders [-360-360] (degrees)
####  * margin [<epsilion>-<maxRange>] (meters)
####  * real-time scans on/off button, or just outside range
controls = dbc.Card(
    [
        html.Div(
            [
                dbc.Label("X variable"),
                dcc.Dropdown(
                    id="xVariable",
                    options=[
                        {"label": col, "value": col} for col in [0, 1, 2, 3, 4]
                    ],
                    value="X var",
                ),
            ]
        ),
        html.Div(
            [
                dbc.Label("Y variable"),
                dcc.Dropdown(
                    id="yVariable",
                    options=[
                        {"label": col, "value": col} for col in [0, 1, 2, 3, 4]
                    ],
                    value="Y var",
                ),
            ]
        ),
        html.Div(
            [
                dbc.Label("Sample points count"),
                dbc.Input(id="pointsCount", type="number", value=len(xSamples)),
            ]
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
    [
        Input("xVariable", "value"),
        Input("yVariable", "value"),
        Input("pointsCount", "value")
    ],
)
def makeGraph(x, y, samplePoints):
    data = [
        go.Scatter(
            x=xSamples,
            y=ySamples,
            mode="markers",
            marker={"size": 8},
            name="Samples {}".format(c),
        )
        for c in range(samplePoints)
    ]

    layout = {"xaxis": {"title": x}, "yaxis": {"title": y}}

    return go.Figure(data=data, layout=layout)


if __name__ == '__main__':
    app.run_server(debug=True, port=8050)
