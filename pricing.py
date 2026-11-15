from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import NamedTuple, Optional

import config

class DeliveryPrice(NamedTuple):
    net_fuel_price: Decimal
    logistics_cost: Decimal
    excise: Decimal
    vat: Decimal
    total_tax: Decimal
    grand_total: Decimal

def round2(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def discount_rate(volume: Decimal) -> Decimal:
    for limit, rate in sorted(config.DISCOUNT_TIERS, reverse=True):
        if volume > limit:
            return rate
    return Decimal("0.00")

def vat_rate(client: str, delivery_date: date, custom_private_rate: Optional[Decimal] = None) -> Decimal:
    if client == "EXEMPT":
        return config.VAT_EXEMPT
    if custom_private_rate is not None:
        return custom_private_rate
    if delivery_date < config.VAT_CHANGE_DATE:
        return config.VAT_PRIVATE_BEFORE
    return config.VAT_PRIVATE_AFTER

def calculate_delivery(
        fuel_type: str,
        client: str,
        delivery_date: date,
        volume: Decimal,
        distance: Decimal,
        base_price: Decimal,
        custom_private_vat: Optional[Decimal] = None,
        custom_gasoline_excise: Optional[Decimal] = None,
) -> DeliveryPrice:
    net = round2(base_price * volume * (1-discount_rate(volume)))

    logistics = round2(distance * config.DELIVERY_PRICE_PER_KM)
    if volume < config.SMALL_LOAD_LIMIT:
        logistics += config.SMALL_LOAD_PRICE

    excise_rate = config.EXCISE_PER_LITER[fuel_type]
    if fuel_type == "GASOLINE" and custom_gasoline_excise is not None:
        excise_rate = custom_gasoline_excise
    excise = round2(excise_rate * volume)

    rate = vat_rate(client, delivery_date, custom_private_vat)
    vat = round2(rate * (net + logistics + excise))

    total_tax = excise + vat
    grand_total = net + logistics + total_tax

    return DeliveryPrice(net, logistics, excise, vat, total_tax, grand_total)