"""Plotly figure builders shared by the dashboard callbacks."""

import math

import plotly.express as px
import plotly.graph_objects as go

from src.data import DWELL_TIME_ORDER, OBSERVATION_DAY_TYPES


DEFAULT_CHART_MARGINS = {"l": 64, "r": 12, "t": 44, "b": 96}
CHART_GRID_COLOR = "#34434e"
CHART_ZERO_LINE_COLOR = "#52616b"
VISITOR_TYPE_COLORS = {
    "Local": "#72c8b8",
    "Domestic": "#8daee8",
    "International": "#f0b66e",
}

COUNTRY_CHART_VIEWPORT_HEIGHT = 344
COUNTRY_ROWS_VIEWPORT_HEIGHT = 284
COUNTRY_AXIS_HEIGHT = 60
COUNTRY_ROWS_TOP_MARGIN = 18
COUNTRY_Y_TITLE_WIDTH = 24


def apply_chart_theme(fig, height=380, margins=None, legend_options=None):
    """Apply the dashboard's common dark Plotly style."""
    legend = {"title": None}
    if legend_options:
        legend.update(legend_options)

    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(margins or DEFAULT_CHART_MARGINS),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={
            "family": '"Open Sans", verdana, arial, sans-serif',
            "size": 12,
            "color": "#e7edf1",
        },
        legend=legend,
    )
    fig.update_xaxes(gridcolor=CHART_GRID_COLOR, zerolinecolor=CHART_ZERO_LINE_COLOR)
    fig.update_yaxes(gridcolor=CHART_GRID_COLOR, zerolinecolor=CHART_ZERO_LINE_COLOR)
    return fig


def empty_chart_figure(height=380, margins=None):
    """Build a themed, dimension-stable figure without traces or axes."""
    figure = px.bar(template="plotly_dark")
    figure.data = []
    apply_chart_theme(figure, height=height, margins=margins)
    figure.update_layout(showlegend=False)
    figure.update_xaxes(visible=False, showgrid=False, zeroline=False, ticks="")
    figure.update_yaxes(visible=False, showgrid=False, zeroline=False, ticks="")
    return figure


def build_event_overview_chart(totals):
    """Build the grouped observation-date and location bar chart."""
    totals = totals.copy()
    totals["date_label"] = totals["event_date"].map(
        lambda date: (
            f"{date:%d %b %Y}<br>"
            f"{OBSERVATION_DAY_TYPES[date].replace(' day', ' Day')}"
        )
    )
    date_order = totals[["event_date", "date_label"]].drop_duplicates().sort_values("event_date")
    location_order = [
        location for location in ["College Green", "O'Connel Bridge"]
        if location in totals["location"].unique()
    ]
    figure = px.bar(
        totals,
        x="date_label",
        y="visitors",
        color="location",
        barmode="group",
        category_orders={
            "date_label": date_order["date_label"].tolist(),
            "location": location_order,
        },
        color_discrete_map={
            "College Green": "#72c8b8",
            "O'Connel Bridge": "#8daee8",
        },
        labels={
            "date_label": "Observation date",
            "visitors": "Visitor volume",
            "location": "Location",
        },
        template="plotly_dark",
        custom_data=["location"],
    )
    apply_chart_theme(
        figure,
        height=380,
        legend_options={"orientation": "h", "y": 1.05, "yanchor": "bottom", "x": 0},
    )
    figure.update_traces(
        hovertemplate=(
            "Date: %{x}<br>Location: %{customdata[0]}<br>"
            "Visitor volume: %{y:,.2f}<extra></extra>"
        )
    )
    figure.update_xaxes(
        type="category",
        categoryorder="array",
        categoryarray=date_order["date_label"].tolist(),
        title_text="Observation date",
        title_standoff=24,
        ticklabelstandoff=10,
        tickangle=0,
        tickfont={"size": 11},
        showgrid=False,
    )
    figure.update_yaxes(title_text="Visitor volume", tickformat=",.0f")
    figure.update_layout(bargap=0.28, bargroupgap=0.08)
    return figure


def build_dwell_time_chart(totals):
    """Build the ordered horizontal dwell-time distribution chart."""
    margins = {"l": 160, "r": 20, "t": 18, "b": 62}
    figure = px.bar(
        totals,
        x="visitors",
        y="dwell_time",
        orientation="h",
        category_orders={"dwell_time": DWELL_TIME_ORDER},
        labels={"visitors": "Visitor volume", "dwell_time": "Dwell-time category"},
        color_discrete_sequence=["#72c8b8"],
        template="plotly_dark",
    )
    apply_chart_theme(figure, height=390, margins=margins)
    figure.update_traces(
        hovertemplate="Dwell time: %{y}<br>Visitor volume: %{x:,.2f}<extra></extra>"
    )
    figure.update_xaxes(
        title_text="Visitor volume",
        tickformat=",.0f",
        gridcolor=CHART_GRID_COLOR,
        zerolinecolor=CHART_ZERO_LINE_COLOR,
        title_standoff=14,
    )
    figure.update_yaxes(
        title_text="Dwell-time category",
        categoryorder="array",
        categoryarray=DWELL_TIME_ORDER,
        autorange="reversed",
        tickmode="array",
        tickvals=DWELL_TIME_ORDER,
        ticktext=[
            "Unknown /<br>not recorded"
            if category == "Unknown / not recorded"
            else category
            for category in DWELL_TIME_ORDER
        ],
        ticklabelstandoff=8,
        showgrid=False,
    )
    return figure


def build_visitor_type_chart(totals):
    """Build the fixed-domain visitor-type composition doughnut."""
    figure = px.pie(
        totals,
        names="visitor_type",
        values="visitors",
        color="visitor_type",
        hole=0.58,
        category_orders={"visitor_type": list(VISITOR_TYPE_COLORS)},
        color_discrete_map=VISITOR_TYPE_COLORS,
        template="plotly_dark",
    )
    apply_chart_theme(
        figure,
        height=380,
        margins={"l": 24, "r": 24, "t": 18, "b": 18, "autoexpand": False},
    )
    figure.update_traces(
        sort=False,
        domain={"x": [0.08, 0.92], "y": [0.18, 0.98]},
        automargin=False,
        textposition="inside",
        insidetextorientation="horizontal",
        texttemplate="%{percent:.2%}",
        hovertemplate=(
            "%{label}<br>Visitor volume: %{value:,.2f}<br>"
            "Share: %{percent:.2%}<extra></extra>"
        ),
        textfont={"color": "#e7edf1", "size": 11},
    )
    figure.update_layout(
        showlegend=True,
        autosize=True,
        legend={
            "orientation": "h",
            "x": 0.5,
            "xanchor": "center",
            "y": 0.02,
            "yanchor": "bottom",
            "font": {"color": "#e7edf1", "size": 11},
        },
        annotations=[
            {
                "text": "Visitor<br>mix",
                "x": 0.5,
                "y": 0.58,
                "xref": "paper",
                "yref": "paper",
                "xanchor": "center",
                "yanchor": "middle",
                "showarrow": False,
                "font": {"color": "#a2b0ba", "size": 13},
            }
        ],
    )
    return figure


def country_chart_margins():
    """Return the matching margins for country rows and their fixed x-axis."""
    row_margins = {"l": 132, "r": 20, "t": 18, "b": 0, "autoexpand": False}
    axis_margins = {
        "l": 132 + COUNTRY_Y_TITLE_WIDTH,
        "r": 20,
        "t": 0,
        "b": 58,
        "autoexpand": False,
    }
    return row_margins, axis_margins


def build_country_charts(chart_countries, mode):
    """Build scrollable country rows and their aligned fixed bottom axis."""
    row_margins, axis_margins = country_chart_margins()
    figure_height = (
        max(
            COUNTRY_ROWS_VIEWPORT_HEIGHT,
            COUNTRY_ROWS_TOP_MARGIN
            + math.ceil(
                (COUNTRY_ROWS_VIEWPORT_HEIGHT - COUNTRY_ROWS_TOP_MARGIN)
                * len(chart_countries)
                / 10
            ),
        )
        if mode == "all"
        else COUNTRY_ROWS_VIEWPORT_HEIGHT
    )
    figure = px.bar(
        chart_countries,
        x="visitors",
        y="country_of_origin",
        orientation="h",
        labels={"visitors": "Visitor volume", "country_of_origin": "Country of origin"},
        color_discrete_sequence=[VISITOR_TYPE_COLORS["International"]],
        template="plotly_dark",
    )
    apply_chart_theme(figure, height=figure_height, margins=row_margins)
    figure.update_traces(
        showlegend=False,
        hovertemplate="Country: %{y}<br>Visitors: %{x:,.0f}<extra></extra>",
    )
    figure.update_xaxes(
        visible=False,
        showticklabels=False,
        showgrid=False,
        zeroline=False,
        title_text=None,
    )
    figure.update_yaxes(
        title_text=None,
        categoryorder="array",
        categoryarray=chart_countries["country_of_origin"].tolist(),
        autorange="reversed",
        ticklabelstandoff=8,
        showgrid=False,
    )

    maximum = float(chart_countries["visitors"].max())
    raw_step = maximum / 6
    magnitude = 10 ** math.floor(math.log10(raw_step))
    tick_step = magnitude * next(
        nice for nice in (1, 2, 2.5, 5, 10) if nice >= raw_step / magnitude
    )
    axis_maximum = math.ceil((maximum * 1.08) / tick_step) * tick_step
    tick_values = [tick_step * index for index in range(int(axis_maximum / tick_step) + 1)]
    shared_range = [0, axis_maximum]
    figure.update_xaxes(domain=[0, 1], range=shared_range, autorange=False)
    figure.update_layout(showlegend=False, bargap=0.22)

    axis_figure = go.Figure()
    apply_chart_theme(axis_figure, height=COUNTRY_AXIS_HEIGHT, margins=axis_margins)
    axis_figure.update_layout(showlegend=False, autosize=True)
    axis_figure.update_xaxes(
        domain=[0, 1],
        range=shared_range,
        autorange=False,
        tickmode="array",
        tickvals=tick_values,
        tickformat=",.0f",
        title_text="Visitor volume",
        title_standoff=14,
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor=CHART_ZERO_LINE_COLOR,
    )
    axis_figure.update_yaxes(visible=False, range=[0, 1], showgrid=False, zeroline=False)
    return figure, {"height": f"{figure_height}px"}, axis_figure
