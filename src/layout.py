"""Declarative Dash layout for the visitor insights dashboard."""

from dash import dcc, html

from src.charts import (
    COUNTRY_AXIS_HEIGHT,
    COUNTRY_CHART_VIEWPORT_HEIGHT,
    COUNTRY_ROWS_VIEWPORT_HEIGHT,
)


EMPTY_FILTER_MESSAGE = "Choose at least one date and one location"


def dashboard_section(title, description, panels, class_name="dashboard-section"):
    """Build a titled dashboard section containing one or more chart cards."""
    return html.Section(
        className=class_name,
        children=[
            html.Div(
                className="section-heading",
                children=[html.H2(title), html.P(description)],
            ),
            html.Div(className="chart-grid", children=panels),
        ],
    )


def filter_chart_panel(title, description, chart_id, height):
    """Build a standard chart card with the shared HTML empty-state overlay."""
    return html.Div(
        className="chart-card",
        children=[
            html.H3(title, className="chart-title"),
            html.P(description, className="chart-description"),
            html.Div(
                className="chart-visualization",
                children=[
                    dcc.Graph(
                        id=chart_id,
                        figure={},
                        config={"displayModeBar": False},
                        responsive=True,
                        style={"height": f"{height}px"},
                    ),
                    html.Div(
                        EMPTY_FILTER_MESSAGE,
                        id=f"{chart_id}-empty-state",
                        className="chart-empty-overlay",
                    ),
                ],
            ),
        ],
    )


def country_origins_panel():
    """Build the country ranking card, including its fixed axis and mode switch."""
    return html.Div(
        className="chart-card country-origins-card",
        children=[
            html.H3("Top countries of origin", className="chart-title"),
            html.P(
                [
                    html.Strong("International visitors only"),
                    " — ranked by summed visitor volume.",
                    html.Br(),
                    "Local and Domestic visitors are excluded.",
                ],
                className="chart-description",
            ),
            dcc.RadioItems(
                id="country-origins-mode",
                options=[
                    {"label": "Top 10", "value": "top10"},
                    {"label": "All Countries", "value": "all"},
                ],
                value="top10",
                inline=True,
                className="country-mode-toggle",
                inputClassName="country-mode-input",
                labelClassName="country-mode-option",
            ),
            html.Div(
                className="chart-visualization country-chart-visualization",
                style={"height": f"{COUNTRY_CHART_VIEWPORT_HEIGHT}px"},
                children=[
                    html.Div(
                        className="country-chart-rows",
                        style={"height": f"{COUNTRY_ROWS_VIEWPORT_HEIGHT}px"},
                        children=[
                            html.Div(
                                "Country of origin (Top 10)",
                                id="country-origin-y-title",
                                className="country-y-axis-title",
                            ),
                            html.Div(
                                className="country-chart-scroll",
                                children=dcc.Graph(
                                    id="country-origins-chart",
                                    figure={},
                                    config={"displayModeBar": False},
                                    responsive=True,
                                    style={
                                        "height": f"{COUNTRY_ROWS_VIEWPORT_HEIGHT}px",
                                        "width": "100%",
                                    },
                                ),
                            ),
                            html.Div(
                                id="country-scroll-hint",
                                className="country-scroll-hint",
                                **{"aria-hidden": "true"},
                                children=html.Div(
                                    className="country-scroll-hint-content",
                                    children=[
                                        html.Span("⌄", className="country-scroll-hint-chevron"),
                                        html.Span("Scroll to view all countries"),
                                    ],
                                ),
                            ),
                        ],
                    ),
                    dcc.Graph(
                        id="country-origins-axis",
                        figure={},
                        config={"displayModeBar": False},
                        responsive=True,
                        className="country-axis-footer",
                        style={"height": f"{COUNTRY_AXIS_HEIGHT}px"},
                    ),
                    html.Div(
                        EMPTY_FILTER_MESSAGE,
                        id="country-origins-chart-empty-state",
                        className="chart-empty-overlay",
                    ),
                ],
            ),
        ],
    )


def build_layout(data, parade_vs_normal_change):
    """Build the complete dashboard layout from the loaded dataset."""
    date_values = sorted(data["event_date"].drop_duplicates())
    date_options = [
        {"label": date.strftime("%d %B %Y"), "value": date.strftime("%Y-%m-%d")}
        for date in date_values
    ]
    location_values = sorted(data["location"].dropna().unique().tolist())
    location_options = [{"label": location, "value": location} for location in location_values]

    return html.Main(
        className="page-shell",
        children=[
            html.Header(
                className="page-header",
                children=[
                    html.Div("DUBLIN CITY CENTRE · VISITOR INSIGHTS", className="eyebrow"),
                    html.H1("Visitor activity dashboard"),
                    html.P(
                        "Explore visitor volumes, dwell-time patterns and visitor origins "
                        "across the available St Patrick’s Day observations.",
                        className="page-description",
                    ),
                    html.P(
                        "The sample covers three observation dates and two locations. "
                        "It does not include hourly counts or site capacity data.",
                        className="scope-note",
                    ),
                ],
            ),
            html.Div(className="filter-sticky-sentinel", **{"aria-hidden": "true"}),
            html.Section(
                className="filter-card",
                **{"aria-labelledby": "filters-heading"},
                children=[
                    html.Div(
                        className="filter-intro",
                        children=[
                            html.H2("Filters", id="filters-heading"),
                            html.P("Choose the observation dates and locations to explore."),
                        ],
                    ),
                    html.Div(
                        className="filter-controls",
                        children=[
                            html.Div(
                                className="filter-field",
                                children=[
                                    html.Label("Observation dates", htmlFor="date-filter"),
                                    dcc.Dropdown(
                                        id="date-filter",
                                        options=date_options,
                                        value=[option["value"] for option in date_options],
                                        multi=True,
                                        clearable=True,
                                        placeholder="Select one or more dates",
                                    ),
                                ],
                            ),
                            html.Div(
                                className="filter-field",
                                children=[
                                    html.Label("Locations", htmlFor="location-filter"),
                                    dcc.Dropdown(
                                        id="location-filter",
                                        options=location_options,
                                        value=location_values,
                                        multi=True,
                                        clearable=True,
                                        placeholder="Select one or more locations",
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Section(
                className="kpi-section",
                **{"aria-labelledby": "kpi-heading"},
                children=[
                    html.Div(
                        className="section-heading compact-heading",
                        children=[
                            html.H2("At a glance", id="kpi-heading"),
                            html.P("Filter-responsive totals alongside a fixed 2025 reference comparison."),
                        ],
                    ),
                    html.Div(
                        className="kpi-grid",
                        children=[
                            html.Div(
                                className="kpi-card",
                                children=[
                                    html.P("Visitor volume"),
                                    html.Strong("—", id="visitor-volume-value", role="status"),
                                    html.Span("Visitors"),
                                ],
                            ),
                            html.Div(
                                className="kpi-card",
                                children=[
                                    html.P("International share"),
                                    html.Strong("—", id="international-share-value", role="status"),
                                    html.Div(
                                        id="visitor-type-stacked-bar",
                                        className="kpi-stacked-bar",
                                        role="img",
                                        **{"aria-label": "Visitor type shares"},
                                    ),
                                    html.Div(
                                        id="visitor-type-share-legend",
                                        className="kpi-share-legend",
                                        **{"aria-live": "polite"},
                                    ),
                                ],
                            ),
                            html.Div(
                                className="kpi-card",
                                children=[
                                    html.P("2025 parade vs normal"),
                                    html.Strong(f"{parade_vs_normal_change:+.2f}%"),
                                    html.Span("17 Mar 2025 vs 10 Mar 2025"),
                                    html.Small(
                                        "Fixed reference · both locations · independent of filters",
                                        className="kpi-note",
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="overview-behaviour-grid",
                children=[
                    dashboard_section(
                        "Event Overview",
                        "Compare estimated visitor volumes across the observed dates and monitored locations.",
                        [
                            filter_chart_panel(
                                "Visitor volume by observation date and location",
                                "Each date is shown as a discrete observation. Values are summed visitor volume.",
                                "event-overview-chart",
                                380,
                            )
                        ],
                        class_name="dashboard-section paired-dashboard-section",
                    ),
                    dashboard_section(
                        "Visitor Behaviour",
                        "Review visitor volume across the dwell-time bands supplied in the source data.",
                        [
                            filter_chart_panel(
                                "Dwell-time distribution",
                                "Visitor volume by supplied duration band, including unknown or unrecorded values.",
                                "dwell-time-chart",
                                390,
                            )
                        ],
                        class_name="dashboard-section paired-dashboard-section",
                    ),
                ],
            ),
            dashboard_section(
                "Visitor Profile & Origins",
                "Understand visitor-type composition and the countries represented in the sample.",
                [
                    filter_chart_panel(
                        "Visitor type composition",
                        "Share of summed visitor volume across Local, Domestic and International groups.",
                        "visitor-type-chart",
                        380,
                    ),
                    country_origins_panel(),
                ],
            ),
            html.Footer(
                "Visitor volume is an estimate. It does not establish crowd density or safety risk.",
                className="page-footer",
            ),
        ],
    )
