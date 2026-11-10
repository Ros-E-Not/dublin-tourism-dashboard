# Dublin City Centre — Visitor Insights Dashboard

An interactive dashboard built with Python, Dash and Plotly to explore visitor activity at two Dublin city-centre locations around St Patrick’s Day.

The dashboard helps users compare visitor volumes, understand dwell-time patterns and explore visitor origins using the supplied sample dataset.

## Business Context and Design Decisions

### Intended Users

The dashboard is designed to support three groups of stakeholders:

- **Event Operations** — compare visitor volumes across locations and observation dates to support operational planning and resource allocation.
- **Crowd Safety Teams** — understand how visitor volumes are distributed between locations and identify observations that may require further investigation.
- **Tourism and Visitor Development Teams** — understand the composition of visitors and identify the main international visitor markets.

### Design Decisions

The dashboard focuses on answering a small number of practical questions: how many visitors were observed, how volumes differed between locations and dates, what the visitor mix looked like, and where international visitors came from.

These requirements informed the main design decisions:

- **A small set of KPIs** provides an immediate overview of visitor volume and international visitor share, while a separate comparison highlights the difference between the 2025 parade day and normal day.
- **Global date and location filters** allow stakeholders to explore the data from different perspectives without navigating between separate views.
- **Separate charts for visitor behaviour, visitor profile and international origins** keep the analysis focused and make the results easier to interpret.
- **International origin analysis** excludes local and domestic visitors, since their country of origin is Ireland and including them would distort the international market comparison.
- **A Top 10 / All Countries option** keeps the main view readable while still allowing access to the full breakdown.
- **A dark, compact layout** keeps the dashboard visually consistent and gives priority to the data.

The available dataset contains observations from only three dates across two locations. The dashboard therefore focuses on comparing these specific observations rather than presenting long-term trends or making assumptions about overall event attendance.

## Dashboard features

The dashboard includes three KPI cards and four interactive charts.

### At a glance

- **Visitor Volume** — total estimated visitor volume for the selected dates and locations.
- **International Share** — the percentage of international visitors, with a breakdown of Local, Domestic and International visitor groups.
- **2025 Parade vs Normal** — compares the two 2025 observations. This is a fixed reference KPI and does not change when dashboard filters are used.

### Event Overview

A grouped bar chart comparing visitor volumes across the available observation dates and the two monitored locations.

### Visitor Behaviour

A horizontal bar chart showing visitor volume across the supplied dwell-time categories, including unknown or unrecorded values.

### Visitor Profile & Origins

- **Visitor Type Composition** — the share of Local, Domestic and International visitors.
- **Top Countries of Origin** — ranks countries by estimated visitor volume. Only International visitors are included, excluding Local and Domestic groups. Users can switch between the top 10 countries and all available countries.

### Filters

Global filters allow users to select one or more observation dates and locations. The relevant KPIs and charts update based on the selected values.

## Data and calculations

The dashboard uses the supplied CSV dataset and data dictionary.

- The dataset contains 178,876 records and eight source fields.
- The two monitored locations are College Green and O'Connel Bridge.
- The sample contains three observation dates:
  - 17 March 2024 — Parade Day
  - 10 March 2025 — Normal Day
  - 17 March 2025 — Parade Day

Pandas is used to load, validate, filter and aggregate the data.

All visitor metrics are calculated by **summing the `visitors` field**, rather than counting CSV rows. The source values are estimates and may contain decimal values; displayed KPI values are rounded for readability.

Dwell time is shown using the original duration bands. No exact average stay is calculated from these categories.

## Data limitations

The dashboard is intended for exploratory analysis, not real-time monitoring or safety assessment.

The supplied dataset has several limitations:

- Only three observation dates are available, so it cannot establish reliable long-term trends or seasonality.
- There is no time-of-day information, so hourly patterns and peak periods cannot be analysed.
- Only two locations are covered.
- There is no site-area or capacity information, so visitor volume cannot be used to calculate crowd density or safety thresholds.
- Age and gender data have significant limitations and are not included in the main dashboard views.

Differences between observations are descriptive. The data alone cannot establish what caused them.

## Project structure

```text
Dublin-tourism-dashboard/
│
├── app.py                  # Application entry point
│
├── src/
│   ├── __init__.py
│   ├── data.py              # Data loading and aggregation
│   ├── layout.py            # Dashboard layout and components
│   ├── charts.py            # Plotly charts and shared styling
│   ├── callbacks.py         # Dash callbacks and interactions
│   └── validate_data.py     # Data validation checks
│
├── assets/
│   ├── filter-sticky.js     # Sticky filter behaviour
│   └── styles.css           # Dashboard styling
│
├── data/
│   ├── Tourism Sample Data 2026.csv
│   └── Tourism Sample Data Dictionary 2026.csv
│
├── requirements.txt
└── README.md
```

The code is organised by responsibility:

- `data.py` handles the dataset and its aggregations.
- `layout.py` defines the dashboard interface.
- `charts.py` builds the Plotly figures.
- `callbacks.py` connects user interactions with data updates and charts.
- `app.py` initialises and runs the Dash application.

## Setup and running

Python 3.10 or later is recommended.

### 1. Clone the repository

```bash
git clone <repository-url>
cd Dublin-tourism-dashboard
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

On macOS and Linux:

```bash
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the dashboard

Development mode is enabled by default:

```bash
python app.py
```

Open the local address shown in the terminal, usually:

```text
http://127.0.0.1:8050
```

## Development and production modes

The application uses the `DASH_ENV` environment variable to select its running mode.

**Development mode** (default):

- Debugging enabled.
- Hot reload enabled.
- Dash developer tools available.

**Production mode:**

On macOS and Linux:

```bash
DASH_ENV=production python app.py
```

On Windows PowerShell:

```powershell
$env:DASH_ENV="production"
python app.py
```

Production mode disables debugging and hot reload.

## Data validation

The project includes a separate validation script to check the data loading and aggregation logic against reference values calculated from the supplied dataset.

Run it with:

```bash
python -m src.validate_data
```

The checks cover data totals, date classification, filtering, aggregation and handling of unknown categories.

All 16 validation checks currently pass.
