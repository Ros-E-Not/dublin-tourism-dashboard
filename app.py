"""Entry point for the Dublin City Centre Visitor Insights dashboard."""

import os

from dash import Dash

from src.callbacks import fixed_parade_vs_normal_change, register_callbacks
from src.data import load_data
from src.layout import build_layout


DATA = load_data()
PARADE_VS_NORMAL_CHANGE = fixed_parade_vs_normal_change(DATA)

app = Dash(__name__, title="Dublin Visitor Insights")
app.layout = build_layout(DATA, PARADE_VS_NORMAL_CHANGE)
register_callbacks(app, DATA)


if __name__ == "__main__":
    is_development = os.getenv("DASH_ENV", "development").strip().lower() != "production"
    app.run(debug=is_development, dev_tools_hot_reload=is_development)
