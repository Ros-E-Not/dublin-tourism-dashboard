"""Load, validate, normalise, and aggregate the supplied visitor CSV."""

from __future__ import annotations

from collections.abc import Iterable as IterableABC
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "Tourism Sample Data 2026.csv"

EXPECTED_COLUMNS = {
    "location",
    "event_date",
    "gender",
    "age_band",
    "dwell_time",
    "visitors",
    "country_of_origin",
    "visitor_type",
}
COLUMN_ORDER = [
    "location",
    "event_date",
    "gender",
    "age_band",
    "dwell_time",
    "visitors",
    "country_of_origin",
    "visitor_type",
]

# Classification is explicit: calendar rules could misclassify other years or
# observations that are not represented in this assessment sample.
OBSERVATION_DAY_TYPES = {
    pd.Timestamp("2024-03-17"): "Parade day",
    pd.Timestamp("2025-03-10"): "Normal day",
    pd.Timestamp("2025-03-17"): "Parade day",
}

DWELL_TIME_ORDER = [
    "0-10 min",
    "10-30 min",
    "30-60 min",
    "60-120 min",
    "120-240 min",
    "240-480 min",
    "480-600 min",
    "> 600 min",
    "Unknown / not recorded",
]

VISITOR_TYPES = ["Local", "Domestic", "International"]


class DataValidationError(ValueError):
    """Raised when source data violates assumptions needed by the dashboard."""


def _normalise_text(series: pd.Series) -> pd.Series:
    """Trim categorical text and convert empty CSV cells to missing values."""
    values = series.astype("string").str.strip()
    return values.mask(values.eq(""), pd.NA)


def _as_filter_values(values: Iterable | str | pd.Timestamp) -> list:
    """Treat scalar strings/dates as one filter value; materialise iterables."""
    if isinstance(values, (str, bytes, pd.Timestamp)) or not isinstance(values, IterableABC):
        return [values]
    return list(values)


def load_data(path: str | Path = DEFAULT_DATA_PATH) -> pd.DataFrame:
    """Read the assessment CSV and return validated, dashboard-ready rows.

    ``age_band``'s source value ``N/A`` means unavailable and is represented
    with Pandas' missing-value marker. The source ``dwell_time`` value
    ``null`` means unknown/not recorded and is retained as a visible category.
    ``gender == 'N'`` means none stated; it is a real source category, not NA.
    """
    csv_path = Path(path)
    if not csv_path.is_file():
        raise FileNotFoundError(f"Visitor data CSV was not found: {csv_path}")

    try:
        # Disable Pandas' broad NA vocabulary so the source's literal ``null``
        # marker can be distinguished from a blank cell and preserved below.
        frame = pd.read_csv(
            csv_path,
            encoding="utf-8-sig",
            dtype={"event_date": "string"},
            keep_default_na=False,
        )
    except (OSError, UnicodeError, pd.errors.ParserError) as exc:
        raise DataValidationError(f"Could not read visitor data CSV: {exc}") from exc

    actual_columns = set(frame.columns)
    missing_columns = EXPECTED_COLUMNS - actual_columns
    extra_columns = actual_columns - EXPECTED_COLUMNS
    if missing_columns or extra_columns:
        details = []
        if missing_columns:
            details.append(f"missing columns: {sorted(missing_columns)}")
        if extra_columns:
            details.append(f"unexpected columns: {sorted(extra_columns)}")
        raise DataValidationError("CSV schema mismatch (" + "; ".join(details) + ")")

    # Keep a predictable field order even if a source export reorders headers.
    frame = frame[COLUMN_ORDER].copy()
    raw_dwell_values = frame["dwell_time"].copy()
    categorical_columns = [
        "location",
        "gender",
        "age_band",
        "dwell_time",
        "country_of_origin",
        "visitor_type",
    ]
    for column in categorical_columns:
        frame[column] = _normalise_text(frame[column])

    # Treat both common spellings of an unavailable value as missing first;
    # dwell_time gets its own explicit, visible unknown category below.
    for column in categorical_columns:
        frame[column] = frame[column].mask(
            frame[column].str.casefold().isin({"n/a", "null"}), pd.NA
        )
    unknown_dwell_mask = (
        _normalise_text(raw_dwell_values).str.casefold().eq("null").fillna(False)
    )
    # Use source positions to distinguish the special dwell ``null`` marker
    # from genuinely blank values while retaining those as missing data.
    frame.loc[unknown_dwell_mask.to_numpy(), "dwell_time"] = "Unknown / not recorded"

    raw_dates = _normalise_text(frame["event_date"])
    parsed_dates = pd.to_datetime(raw_dates, format="%d/%m/%Y", errors="coerce")
    invalid_dates = raw_dates.isna() | parsed_dates.isna()
    if invalid_dates.any():
        examples = raw_dates[invalid_dates].head(5).tolist()
        raise DataValidationError(
            f"event_date contains {int(invalid_dates.sum())} blank or invalid value(s); "
            f"examples: {examples}"
        )
    frame["event_date"] = parsed_dates.dt.normalize()

    numeric_visitors = pd.to_numeric(frame["visitors"], errors="coerce")
    invalid_visitors = numeric_visitors.isna()
    if invalid_visitors.any():
        raise DataValidationError(
            f"visitors contains {int(invalid_visitors.sum())} blank or non-numeric value(s)"
        )
    if not np.isfinite(numeric_visitors.to_numpy()).all():
        raise DataValidationError("visitors contains a non-finite value")
    if numeric_visitors.lt(0).any():
        raise DataValidationError("visitors contains negative values")
    frame["visitors"] = numeric_visitors.astype("float64")

    required_dimensions = ["location", "country_of_origin", "visitor_type", "dwell_time"]
    missing_dimensions = frame[required_dimensions].isna().sum()
    if missing_dimensions.any():
        summary = {key: int(value) for key, value in missing_dimensions.items() if value}
        raise DataValidationError(f"Required categorical values are missing: {summary}")

    unmapped_dates = sorted(set(frame["event_date"]) - set(OBSERVATION_DAY_TYPES))
    if unmapped_dates:
        formatted = [date.strftime("%d/%m/%Y") for date in unmapped_dates]
        raise DataValidationError(f"Found observation date(s) without an explicit classification: {formatted}")
    frame["day_type"] = frame["event_date"].map(OBSERVATION_DAY_TYPES).astype("category")

    unknown_dwell_categories = set(frame["dwell_time"].dropna().unique()) - set(DWELL_TIME_ORDER)
    if unknown_dwell_categories:
        raise DataValidationError(
            f"Unrecognised dwell_time categories: {sorted(unknown_dwell_categories)}"
        )
    frame["dwell_time"] = pd.Categorical(
        frame["dwell_time"], categories=DWELL_TIME_ORDER, ordered=True
    )

    if not frame["visitor_type"].isin(VISITOR_TYPES).all():
        invalid_types = sorted(set(frame["visitor_type"]) - set(VISITOR_TYPES))
        raise DataValidationError(f"Unrecognised visitor_type value(s): {invalid_types}")

    return frame


def aggregate_visitors(
    frame: pd.DataFrame,
    by: str | Sequence[str],
    *,
    locations: Iterable[str] | None = None,
    dates: Iterable[str | pd.Timestamp] | None = None,
    visitor_types: Iterable[str] | None = None,
    observed: bool = True,
) -> pd.DataFrame:
    """Sum visitor volume by dimensions after applying optional filters.

    This is the shared aggregation path for later dashboard views. Filters
    narrow source rows first; ``groupby(...).sum()`` then adds the weighted
    ``visitors`` measure instead of counting records.
    """
    dimensions = [by] if isinstance(by, str) else list(by)
    if not dimensions:
        raise ValueError("At least one grouping dimension is required")
    unknown = set(dimensions) - set(frame.columns)
    if unknown:
        raise ValueError(f"Unknown grouping dimension(s): {sorted(unknown)}")

    selected = frame
    if locations is not None:
        selected = selected[selected["location"].isin(_as_filter_values(locations))]
    if dates is not None:
        parsed_filter_dates = pd.to_datetime(_as_filter_values(dates), errors="raise").normalize()
        selected = selected[selected["event_date"].isin(parsed_filter_dates)]
    if visitor_types is not None:
        selected = selected[selected["visitor_type"].isin(_as_filter_values(visitor_types))]

    return (
        selected.groupby(dimensions, observed=observed, dropna=False, as_index=False)["visitors"]
        .sum()
        .sort_values(dimensions, kind="stable", ignore_index=True)
    )


def aggregate_country_origins(
    frame: pd.DataFrame,
    *,
    locations: Iterable[str] | None = None,
    dates: Iterable[str | pd.Timestamp] | None = None,
    visitor_types: Iterable[str] = ("International",),
) -> pd.DataFrame:
    """Aggregate countries, defaulting to international visitors only."""
    return aggregate_visitors(
        frame,
        "country_of_origin",
        locations=locations,
        dates=dates,
        visitor_types=visitor_types,
    ).sort_values("visitors", ascending=False, ignore_index=True)

