from datetime import date
from decimal import Decimal

DISCOUNT_TIERS = [
    (Decimal ("5000"), Decimal ("0.05")),
    (Decimal ("20000"), Decimal ("0.10")),
]

DELIVERY_PRICE_PER_KM = Decimal ("1.80")

SMALL_LOAD_LIMIT = Decimal ("1000")
SMALL_LOAD_PRICE = Decimal ("150")

EXCISE_PER_LITER = {
    "GASOLINE": Decimal ("0.47"),
    "DIESEL": Decimal ("0.33"),
    "LPG": Decimal ("0.18"),
}

VAT_EXEMPT = Decimal ("0.00")
VAT_PRIVATE_BEFORE = Decimal ("0.21")
VAT_PRIVATE_AFTER = Decimal ("0.23")
VAT_CHANGE_DATE = date (2024, 1, 1)