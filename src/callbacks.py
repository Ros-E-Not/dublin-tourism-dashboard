"""Dash callback registration and filter-driven dashboard updates."""

from dash import Input, Output, html

from src.charts import (
    COUNTRY_AXIS_HEIGHT,
    COUNTRY_ROWS_VIEWPORT_HEIGHT,
    VISITOR_TYPE_COLORS,
    build_country_charts,
    build_dwell_time_chart,
    build_event_overview_chart,
    build_visitor_type_chart,
    country_chart_margins,
    empty_chart_figure,
)
from src.data import aggregate_country_origins, aggregate_visitors
from src.layout import EMPTY_FILTER_MESSAGE


def fixed_parade_vs_normal_change(data):
    """Calculate the static 2025 reference KPI outside global filter callbacks."""
    normal_day_volume = aggregate_visitors(
        data,
        by="event_date",
        dates=["2025-03-10"],
    )["visitors"].sum()
    parade_day_volume = aggregate_visitors(
        data,
        by="event_date",
        dates=["2025-03-17"],
    )["visitors"].sum()
    return (parade_day_volume - normal_day_volume) / normal_day_volume * 100


def visitor_volume_value(data, selected_dates, selected_locations):
    """Return the filtered visitor-volume KPI text."""
    if not selected_dates or not selected_locations:
        return EMPTY_FILTER_MESSAGE
    totals = aggregate_visitors(
        data,
        by=["event_date", "location"],
        dates=selected_dates,
        locations=selected_locations,
    )
    return f"{totals['visitors'].sum():,.0f}"


def international_share_content(data, selected_dates, selected_locations):
    """Return the filtered International-share KPI and stacked composition bar."""
    if not selected_dates or not selected_locations:
        return "—", [], EMPTY_FILTER_MESSAGE, EMPTY_FILTER_MESSAGE

    totals = aggregate_visitors(
        data,
        by="visitor_type",
        dates=selected_dates,
        locations=selected_locations,
    )
    volumes = dict(zip(totals["visitor_type"], totals["visitors"]))
    total_volume = sum(volumes.values())
    if total_volume <= 0:
        return "—", [], EMPTY_FILTER_MESSAGE, "No visitor volume for the selected filters"

    shares = {
        visitor_type: volumes.get(visitor_type, 0) / total_volume * 100
        for visitor_type in VISITOR_TYPE_COLORS
    }
    stacked_segments = [
        html.Div(
            className="kpi-stack-segment",
            style={
                "width": f"{shares[visitor_type]:.6f}%",
                "backgroundColor": color,
            },
            title=f"{visitor_type}: {shares[visitor_type]:.2f}%",
        )
        for visitor_type, color in VISITOR_TYPE_COLORS.items()
    ]
    legend_items = [
        html.Span(
            className="kpi-share-item",
            children=[
                html.Span(
                    className="kpi-share-swatch",
                    style={"backgroundColor": color},
                    **{"aria-hidden": "true"},
                ),
                f"{visitor_type} {shares[visitor_type]:.1f}%",
            ],
        )
        for visitor_type, color in VISITOR_TYPE_COLORS.items()
    ]
    aria_label = "; ".join(
        f"{visitor_type}: {shares[visitor_type]:.1f}%"
        for visitor_type in VISITOR_TYPE_COLORS
    )
    return f"{shares['International']:.2f}%", stacked_segments, aria_label, legend_items


def event_overview_content(data, selected_dates, selected_locations):
    """Return the Event Overview figure and its overlay state."""
    if not selected_dates or not selected_locations:
        return empty_chart_figure(height=380), EMPTY_FILTER_MESSAGE, {"display": "flex"}
    totals = aggregate_visitors(
        data,
        by=["event_date", "location"],
        dates=selected_dates,
        locations=selected_locations,
    )
    if totals.empty:
        return empty_chart_figure(height=380), "No observations match the selected filters", {"display": "flex"}
    return build_event_overview_chart(totals), "", {"display": "none"}


def dwell_time_content(data, selected_dates, selected_locations):
    """Return the dwell-time figure and its overlay state."""
    margins = {"l": 160, "r": 20, "t": 18, "b": 62}
    if not selected_dates or not selected_locations:
        return empty_chart_figure(height=390, margins=margins), EMPTY_FILTER_MESSAGE, {"display": "flex"}
    totals = aggregate_visitors(
        data,
        by=["dwell_time"],
        dates=selected_dates,
        locations=selected_locations,
    )
    if totals.empty:
        return empty_chart_figure(height=390, margins=margins), "No observations match the selected filters", {"display": "flex"}
    return build_dwell_time_chart(totals), "", {"display": "none"}


def visitor_type_content(data, selected_dates, selected_locations):
    """Return the visitor-type doughnut and its overlay state."""
    if not selected_dates or not selected_locations:
        return empty_chart_figure(height=380), EMPTY_FILTER_MESSAGE, {"display": "flex"}
    totals = aggregate_visitors(
        data,
        by=["visitor_type"],
        dates=selected_dates,
        locations=selected_locations,
    )
    if totals.empty:
        return empty_chart_figure(height=380), "No observations match the selected filters", {"display": "flex"}
    return build_visitor_type_chart(totals), "", {"display": "none"}


def country_origins_content(data, selected_dates, selected_locations, mode="top10"):
    """Return country rows, the fixed x-axis, and empty-state content."""
    row_margins, axis_margins = country_chart_margins()
    y_axis_title = (
        "Country of origin (All Countries)"
        if mode == "all"
        else "Country of origin (Top 10)"
    )
    if not selected_dates or not selected_locations:
        return (
            empty_chart_figure(height=COUNTRY_ROWS_VIEWPORT_HEIGHT, margins=row_margins),
            {"height": f"{COUNTRY_ROWS_VIEWPORT_HEIGHT}px"},
            empty_chart_figure(height=COUNTRY_AXIS_HEIGHT, margins=axis_margins),
            y_axis_title,
            "country-scroll-hint",
            EMPTY_FILTER_MESSAGE,
            {"display": "flex"},
        )

    totals = aggregate_country_origins(data, dates=selected_dates, locations=selected_locations)
    chart_countries = (
        totals
        if mode == "all"
        else totals.loc[totals["country_of_origin"].ne("Other")].head(10)
    )
    if chart_countries.empty:
        return (
            empty_chart_figure(height=COUNTRY_ROWS_VIEWPORT_HEIGHT, margins=row_margins),
            {"height": f"{COUNTRY_ROWS_VIEWPORT_HEIGHT}px"},
            empty_chart_figure(height=COUNTRY_AXIS_HEIGHT, margins=axis_margins),
            y_axis_title,
            "country-scroll-hint",
            "No country origins match the selected filters",
            {"display": "flex"},
        )

    figure, graph_style, axis_figure = build_country_charts(chart_countries, mode)
    return (
        figure,
        graph_style,
        axis_figure,
        y_axis_title,
        "country-scroll-hint is-visible" if mode == "all" else "country-scroll-hint",
        "",
        {"display": "none"},
    )


def register_callbacks(app, data):
    """Register all dashboard callbacks against one in-memory dataset."""

    @app.callback(
        Output("visitor-volume-value", "children"),
        Input("date-filter", "value"),
        Input("location-filter", "value"),
    )
    def update_visitor_volume(selected_dates, selected_locations):
        return visitor_volume_value(data, selected_dates, selected_locations)

    @app.callback(
        Output("international-share-value", "children"),
        Output("visitor-type-stacked-bar", "children"),
        Output("visitor-type-stacked-bar", "aria-label"),
        Output("visitor-type-share-legend", "children"),
        Input("date-filter", "value"),
        Input("location-filter", "value"),
    )
    def update_international_share(selected_dates, selected_locations):
        return international_share_content(data, selected_dates, selected_locations)

    @app.callback(
        Output("event-overview-chart", "figure"),
        Output("event-overview-chart-empty-state", "children"),
        Output("event-overview-chart-empty-state", "style"),
        Input("date-filter", "value"),
        Input("location-filter", "value"),
    )
    def update_event_overview(selected_dates, selected_locations):
        return event_overview_content(data, selected_dates, selected_locations)

    @app.callback(
        Output("dwell-time-chart", "figure"),
        Output("dwell-time-chart-empty-state", "children"),
        Output("dwell-time-chart-empty-state", "style"),
        Input("date-filter", "value"),
        Input("location-filter", "value"),
    )
    def update_dwell_time(selected_dates, selected_locations):
        return dwell_time_content(data, selected_dates, selected_locations)

    @app.callback(
        Output("visitor-type-chart", "figure"),
        Output("visitor-type-chart-empty-state", "children"),
        Output("visitor-type-chart-empty-state", "style"),
        Input("date-filter", "value"),
        Input("location-filter", "value"),
    )
    def update_visitor_type(selected_dates, selected_locations):
        return visitor_type_content(data, selected_dates, selected_locations)

    @app.callback(
        Output("country-origins-chart", "figure"),
        Output("country-origins-chart", "style"),
        Output("country-origins-axis", "figure"),
        Output("country-origin-y-title", "children"),
        Output("country-scroll-hint", "className"),
        Output("country-origins-chart-empty-state", "children"),
        Output("country-origins-chart-empty-state", "style"),
        Input("date-filter", "value"),
        Input("location-filter", "value"),
        Input("country-origins-mode", "value"),
    )
    def update_country_origins(selected_dates, selected_locations, mode):
        return country_origins_content(data, selected_dates, selected_locations, mode)
