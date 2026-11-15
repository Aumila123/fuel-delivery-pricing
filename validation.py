import re
from datetime import date
from decimal import Decimal
from typing import Any, NamedTuple, Optional, Set
import config

MISSING_FIELD = "MISSING_FIELD"
UNKNOWN_TYPE = "UNKNOWN_TYPE"
UNKNOWN_CLIENT = "UNKNOWN_CLIENT"
INVALID_DATE = "INVALID_DATE"
INVALID_VALUE = "INVALID_VALUE"
DUPLICATE_ID = "DUPLICATE_ID"

REQUIRED_FIELDS = ("id", "type", "client", "date", "volume", "distance", "basePrice")
VALID_TYPES = set(config.EXCISE_PER_LITER)
VALID_CLIENTS = {"PRIVATE", "EXEMPT"}

_ISO_DATE = re.compile(r"(\d{4})-(\d{2})-(\d{2})", re.ASCII)
_EU_DATE = re.compile(r"(\d{2})/(\d{2})/(\d{4})", re.ASCII)


class Shipment(NamedTuple):
    id: str
    type: str
    client: str
    date: date
    volume: Decimal
    distance: Decimal
    base_price: Decimal


class Result(NamedTuple):
    shipment: Optional[Shipment]
    error: Optional[str]
    shipment_id: str


def parse_date(text: Any) -> Optional[date]:
    if not isinstance(text, str):
        return None
    match = _ISO_DATE.fullmatch(text)
    if match:
        year, month, day = (int(g) for g in match.groups())
    else:
        match = _EU_DATE.fullmatch(text)
        if not match:
            return None
        day, month, year = (int(g) for g in match.groups())
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _to_decimal(value: Any) -> Optional[Decimal]:
    """A real JSON number -> Decimal. Text, bool, null, NaN, Infinity -> None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, Decimal):
        number = value
    elif isinstance(value, float):
        number = Decimal(str(value))
    else:
        return None
    return number if number.is_finite() else None


def validate_record(record: Any, seen_ids: Set[str]) -> Result:
    if not isinstance(record, dict):
        return Result(None, MISSING_FIELD, "")

    raw_id = record.get("id")
    shipment_id = raw_id if isinstance(raw_id, str) else ""

    if isinstance(raw_id, str):
        if raw_id in seen_ids:
            return Result(None, DUPLICATE_ID, shipment_id)
        seen_ids.add(raw_id)

    if any(record.get(field) is None for field in REQUIRED_FIELDS):
        return Result(None, MISSING_FIELD, shipment_id)

    if not isinstance(raw_id, str):
        return Result(None, INVALID_VALUE, shipment_id)

    raw_type = record["type"]
    fuel_type = raw_type.strip().upper() if isinstance(raw_type, str) else None
    if fuel_type not in VALID_TYPES:
        return Result(None, UNKNOWN_TYPE, shipment_id)

    raw_client = record["client"]
    client = raw_client.strip().upper() if isinstance(raw_client, str) else None
    if client not in VALID_CLIENTS:
        return Result(None, UNKNOWN_CLIENT, shipment_id)

    delivery_date = parse_date(record["date"])
    if delivery_date is None:
        return Result(None, INVALID_DATE, shipment_id)

    volume = _to_decimal(record["volume"])
    distance = _to_decimal(record["distance"])
    base_price = _to_decimal(record["basePrice"])
    if (volume is None or distance is None or base_price is None
            or volume <= 0 or distance < 0 or base_price < 0):
        return Result(None, INVALID_VALUE, shipment_id)

    shipment = Shipment(raw_id, fuel_type, client, delivery_date,
                        volume, distance, base_price)
    return Result(shipment, None, shipment_id)