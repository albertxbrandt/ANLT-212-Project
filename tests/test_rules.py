"""Unit tests for replenishment math. These do not touch the database."""

from datetime import date

import pytest

from inventory import (
    consumption_rate,
    days_of_cover,
    restock_reasons,
    suggested_purchase,
    waste_share,
    week_starts,
)


TODAY = date(2026, 10, 7)


def test_consumption_rate_uses_inclusive_span_inside_the_window():
    consumed = {
        date(2026, 10, 1): 4,
        date(2026, 9, 1): 100,
    }
    assert consumption_rate(consumed, TODAY) == pytest.approx(4 / 7)


def test_consumption_rate_includes_the_first_day_of_the_window():
    edge = TODAY.fromordinal(TODAY.toordinal() - 28)
    assert consumption_rate({edge: 5}, TODAY) == pytest.approx(5 / 29)
    day_before = edge.fromordinal(edge.toordinal() - 1)
    assert consumption_rate({day_before: 5}, TODAY) is None


def test_consumption_rate_is_unknown_without_use():
    assert consumption_rate({}, TODAY) is None


def test_days_of_cover():
    assert days_of_cover(4, 2) == pytest.approx(2)
    assert days_of_cover(0, 1) == 0
    assert days_of_cover(4, None) is None
    assert days_of_cover(4, 0) is None


def test_suggested_purchase_takes_the_larger_gap():
    assert suggested_purchase(1, 2, None) == 1
    assert suggested_purchase(1, 2, 1) == 13
    assert suggested_purchase(5, 2, 0.1) == 0


def test_restock_reasons_cover_par_and_a_short_horizon():
    assert restock_reasons(1, 2, None) == ["Below par"]
    assert restock_reasons(5, 2, 6) == ["Less than 7 days of cover"]
    assert restock_reasons(1, 2, 6) == ["Below par", "Less than 7 days of cover"]
    assert restock_reasons(5, 2, 7) == []


def test_waste_share():
    assert waste_share(3, 1) == pytest.approx(0.25)
    assert waste_share(0, 0) is None


def test_week_starts_are_eight_mondays_ending_this_week():
    weeks = week_starts(TODAY)
    assert weeks[0] == date(2026, 8, 17)
    assert weeks[-1] == date(2026, 10, 5)
    assert all(day.weekday() == 0 for day in weeks)
    assert len(weeks) == 8
