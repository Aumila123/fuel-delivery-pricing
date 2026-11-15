import json
import os
from datetime import date
from decimal import Decimal as D

from validation import parse_date, validate_record


def good(**changes):
    record = {"id": "a1", "type": "DIESEL", "client": "PRIVATE", "date": "2024-02-10",
              "volume": 2000, "distance": 40, "basePrice": D("0.9")}
    record.update(changes)
    return record


def err(record, seen=None):
    return validate_record(record, set() if seen is None else seen).error


def test_dates():
    assert parse_date("2024-02-29") == date(2024, 2, 29)     # leap day
    assert parse_date("03/04/2024") == date(2024, 4, 3)      # day first
    assert parse_date("2023-02-30") is None
    assert parse_date("2023-02-29") is None                  # not a leap year
    assert parse_date("31/04/2024") is None
    assert parse_date("2024-13-01") is None
    assert parse_date("2024-1-1") is None                    # wrong format
    assert parse_date("2024/01/01") is None
    assert parse_date("01-01-2024") is None
    assert parse_date("") is None and parse_date(None) is None and parse_date(20240101) is None


def test_valid_and_normalisation():
    r = validate_record(good(type=" diesel ", client="exempt"), set())
    assert r.error is None
    assert r.shipment.type == "DIESEL" and r.shipment.client == "EXEMPT"
    assert r.shipment.volume == D("2000") and r.shipment.base_price == D("0.9")


def test_zero_distance_and_price_allowed():
    assert err(good(distance=0, basePrice=0)) is None


def test_missing_field():
    for field in ("id", "type", "client", "date", "volume", "distance", "basePrice"):
        record = good()
        del record[field]
        assert err(record) == "MISSING_FIELD", field
        assert err(good(**{field: None})) == "MISSING_FIELD", field
    assert validate_record({}, set()).shipment_id == ""
    assert validate_record("text", set()).error == "MISSING_FIELD"
    assert validate_record([], set()).error == "MISSING_FIELD"
    assert validate_record(None, set()).error == "MISSING_FIELD"


def test_unknown_type_and_client():
    assert err(good(type="KEROSENE")) == "UNKNOWN_TYPE"
    assert err(good(type=5)) == "UNKNOWN_TYPE"
    assert err(good(client="GOVERNMENT")) == "UNKNOWN_CLIENT"
    assert err(good(client=["PRIVATE"])) == "UNKNOWN_CLIENT"


def test_invalid_date():
    assert err(good(date="2023-02-30")) == "INVALID_DATE"
    assert err(good(date=20240101)) == "INVALID_DATE"


def test_invalid_value():
    assert err(good(volume=0)) == "INVALID_VALUE"
    assert err(good(volume=-2000)) == "INVALID_VALUE"
    assert err(good(distance=-1)) == "INVALID_VALUE"
    assert err(good(basePrice=D("-0.1"))) == "INVALID_VALUE"
    assert err(good(volume="5000")) == "INVALID_VALUE"
    assert err(good(basePrice="0.9")) == "INVALID_VALUE"
    assert err(good(volume=True)) == "INVALID_VALUE"
    assert err(good(volume=float("nan"))) == "INVALID_VALUE"
    assert err(good(volume=float("inf"))) == "INVALID_VALUE"
    assert err(good(id=123)) == "INVALID_VALUE"


def test_duplicates():
    seen = set()
    assert err(good(id="X"), seen) is None
    assert err(good(id="X"), seen) == "DUPLICATE_ID"
    assert err(good(id="x"), seen) is None


def test_duplicate_of_invalid_first_record():
    seen = set()
    assert err(good(id="Y", type="KEROSENE"), seen) == "UNKNOWN_TYPE"
    assert err(good(id="Y"), seen) == "DUPLICATE_ID"


def test_one_code_per_record():
    assert err(good(type="KEROSENE", date="bad", volume=-1)) == "UNKNOWN_TYPE"
    assert err(good(date="bad", volume=-1)) == "INVALID_DATE"


def test_sample_file():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shipments.json")
    if not os.path.exists(path):
        print("     (shipments.json not found next to the tests, skipped)")
        return
    with open(path, encoding="utf-8") as f:
        records = json.load(f, parse_float=D)
    seen = set()
    results = [validate_record(r, seen) for r in records]
    errors = [x.error for x in results if x.error]
    assert errors == ["UNKNOWN_TYPE", "INVALID_VALUE", "INVALID_DATE",
                      "MISSING_FIELD", "UNKNOWN_CLIENT", "DUPLICATE_ID"], errors
    assert len(results) - len(errors) == 11


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("ok  ", t.__name__)