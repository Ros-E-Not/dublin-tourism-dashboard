"""Run deterministic checks against independently inspected CSV totals."""

from __future__ import annotations

import math
from dataclasses import dataclass

from src.data import (
    DWELL_TIME_ORDER,
    OBSERVATION_DAY_TYPES,
    aggregate_country_origins,
    aggregate_visitors,
    load_data,
)


EXPECTED_ROWS = 178_876
EXPECTED_TOTAL = 2_525_590.254405157
EXPECTED_BY_DATE = {
    "2024-03-17": 972_898.291352,
    "2025-03-10": 775_102.639932,
    "2025-03-17": 777_589.323121,
}
EXPECTED_BY_LOCATION = {
    "College Green": 1_392_484.385794,
    "O'Connel Bridge": 1_133_105.868611,
}
EXPECTED_BY_VISITOR_TYPE = {
    "Local": 1_795_797.970923,
    "Domestic": 336_977.370897,
    "International": 392_814.912585,
}
EXPECTED_AGE_UNAVAILABLE = 1_285_455.335582
EXPECTED_DWELL_UNKNOWN = 7_281.499792
EXPECTED_2025_PARADE_COLLEGE_GREEN_LOCAL = 325_034.273323


@dataclass
class ValidationResult:
    name: str
    passed: bool
    detail: str


def _check_close(name: str, actual: float, expected: float, tolerance: float = 0.01) -> ValidationResult:
    passed = math.isclose(actual, expected, rel_tol=0, abs_tol=tolerance)
    return ValidationResult(
        name,
        passed,
        f"actual={actual:,.6f}; expected={expected:,.6f}; tolerance=±{tolerance:.2f}",
    )


def run_validation() -> list[ValidationResult]:
    """Load the source and compare core row counts and weighted totals."""
    frame = load_data()
    results = [
        ValidationResult(
            "source row count",
            len(frame) == EXPECTED_ROWS,
            f"actual={len(frame):,}; expected={EXPECTED_ROWS:,}",
        ),
        _check_close("overall visitor total", float(frame["visitors"].sum()), EXPECTED_TOTAL),
        ValidationResult(
            "dwell-time logical order",
            list(frame["dwell_time"].cat.categories) == DWELL_TIME_ORDER
            and frame["dwell_time"].cat.ordered,
            f"categories={list(frame['dwell_time'].cat.categories)}; ordered={frame['dwell_time'].cat.ordered}",
        ),
        ValidationResult(
            "explicit date classification",
            frame.groupby("event_date", observed=True)["day_type"].first().to_dict()
            == OBSERVATION_DAY_TYPES,
            f"mapped_dates={frame.groupby('event_date', observed=True)['day_type'].first().to_dict()}",
        ),
    ]

    for date, expected in EXPECTED_BY_DATE.items():
        actual = aggregate_visitors(frame, "event_date", dates=[date])["visitors"].sum()
        results.append(_check_close(f"visitor total on {date}", float(actual), expected))

    for location, expected in EXPECTED_BY_LOCATION.items():
        actual = aggregate_visitors(frame, "location", locations=[location])["visitors"].sum()
        results.append(_check_close(f"visitor total at {location}", float(actual), expected))

    for visitor_type, expected in EXPECTED_BY_VISITOR_TYPE.items():
        actual = aggregate_visitors(frame, "visitor_type", visitor_types=[visitor_type])["visitors"].sum()
        results.append(_check_close(f"visitor total for {visitor_type}", float(actual), expected))

    filtered_volume = aggregate_visitors(
        frame,
        "visitor_type",
        locations=["College Green"],
        dates=["2025-03-17"],
        visitor_types=["Local"],
    )["visitors"].sum()
    results.append(
        _check_close(
            "combined location/date/type filter",
            float(filtered_volume),
            EXPECTED_2025_PARADE_COLLEGE_GREEN_LOCAL,
        )
    )

    age_unavailable = float(frame.loc[frame["age_band"].isna(), "visitors"].sum())
    results.append(_check_close("unavailable age-band volume", age_unavailable, EXPECTED_AGE_UNAVAILABLE))
    dwell_unknown = float(
        frame.loc[frame["dwell_time"] == "Unknown / not recorded", "visitors"].sum()
    )
    results.append(_check_close("unknown dwell-time volume", dwell_unknown, EXPECTED_DWELL_UNKNOWN))

    country_origins = aggregate_visitors(frame, "visitor_type")
    # The dedicated helper applies this default. Exercise it here so changes to
    # its default cannot silently make origins mix local/domestic visitors in.
    countries = aggregate_country_origins(frame)
    international_total = country_origins.loc[
        country_origins["visitor_type"] == "International", "visitors"
    ].sum()
    results.append(
        _check_close(
            "default international-only country total",
            float(countries["visitors"].sum()),
            float(international_total),
        )
    )

    return results


def main() -> int:
    results = run_validation()
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{status}  {result.name}: {result.detail}")
    failures = sum(not result.passed for result in results)
    print(f"\n{len(results) - failures}/{len(results)} validation checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
