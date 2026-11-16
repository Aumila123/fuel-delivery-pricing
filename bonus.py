from datetime import date, timedelta
from decimal import Decimal, localcontext
from typing import Any, Dict, Iterable, List, NamedTuple, Optional, Set, Tuple

import config
from pricing import DeliveryPrice, decimal_precision, round2
from validation import Shipment, parse_date

# ---------- Bonus 1 ----------

def summarize_range(
    priced: Iterable[Tuple[Shipment, DeliveryPrice]], start: date, end: date
) -> Tuple[int, str, Decimal]:
    count = 0
    best_id = "N/A"
    best_total = None
    total_vat = Decimal("0.00")
    for shipment, price in priced:
        if start <= shipment.date <= end:
            count += 1
            with localcontext() as context:
                context.prec = max(context.prec, decimal_precision(total_vat, price.vat))
                total_vat += price.vat
            if best_total is None or price.grand_total > best_total:
                best_total = price.grand_total
                best_id = shipment.id
    return count, best_id, total_vat

# ---------- Bonus 2 ----------
class LateInterest(NamedTuple):
    due_date: date
    days_late: int
    interest: Decimal


def first_usable_payments(payments: List[Any], known_ids: Set[str]) -> Dict[str, date]:
    paid: Dict[str, date] = {}
    for payment in payments:
        if not isinstance(payment, dict):
            continue
        payment_id = payment.get("id")
        if not isinstance(payment_id, str) or payment_id not in known_ids or payment_id in paid:
            continue
        paid_date = parse_date(payment.get("paidDate"))
        if paid_date is not None:
            paid[payment_id] = paid_date
    return paid


def late_interest(grand_total: Decimal, delivery_date: date,
                  paid_date: Optional[date]) -> LateInterest:
    try:
        due = delivery_date + timedelta(days=config.PAYMENT_TERM_DAYS)
    except OverflowError:
        due = date.max
    end = paid_date if paid_date is not None else config.REPORT_DATE

    days_late = max(0, (end - due).days)
    last_old_rate_day = config.LATE_RATE_CHANGE_DATE - timedelta(days=1)
    old_rate_days = max(0, (min(end, last_old_rate_day) - due).days)
    new_rate_days = days_late - old_rate_days

    with localcontext() as context:
        context.prec = decimal_precision(grand_total, extra=32)
        weighted_rate_days = (
            config.LATE_RATE_BEFORE * old_rate_days
            + config.LATE_RATE_FROM * new_rate_days
        )
        interest = round2(
            grand_total * weighted_rate_days / config.DAYS_IN_YEAR
        )
    return LateInterest(due, days_late, interest)