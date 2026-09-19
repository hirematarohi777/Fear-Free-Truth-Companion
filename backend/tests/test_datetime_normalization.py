from datetime import datetime, timezone

from app.services.sharing.family_service import as_utc


def test_naive_mongo_datetime_is_interpreted_as_utc():
    value = datetime(2026, 9, 19, 12, 0, 0)
    normalized = as_utc(value)
    assert normalized.tzinfo == timezone.utc
    assert normalized.hour == 12


def test_aware_datetime_is_converted_to_utc():
    value = datetime(2026, 9, 19, 14, 0, 0, tzinfo=timezone.utc)
    assert as_utc(value) == value


def test_none_datetime_stays_none():
    assert as_utc(None) is None