from datetime import date
from decimal import Decimal as D

import bonus
from pricing import calculate_delivery
from validation import Shipment


def priced_item(sid, day, volume="1000"):
    s = Shipment(sid, "DIESEL", "PRIVATE", day, D(volume), D("0"), D("1"))
    p = calculate_delivery(s.type, s.client, s.date, s.volume, s.distance, s.base_price)
    return s, p


def test_range_inclusive_and_empty():
    items = [priced_item("a", date(2024, 1, 1)), priced_item("b", date(2024, 1, 31)),
             priced_item("c", date(2024, 2, 1))]
    count, best, vat = bonus.summarize_range(items, date(2024, 1, 1), date(2024, 1, 31))
    assert count == 2
    assert vat == items[0][1].vat + items[1][1].vat
    assert bonus.summarize_range(items, date(2025, 1, 1), date(2025, 1, 2)) == (0, "N/A", D("0.00"))


def test_most_expensive_and_tie():
    items = [priced_item("a", date(2024, 1, 5), "1000"), priced_item("b", date(2024, 1, 6), "3000"),
             priced_item("c", date(2024, 1, 7), "3000")]
    assert bonus.summarize_range(items, date(2024, 1, 1), date(2024, 1, 31))[1] == "b"   # tie: first


def test_pdf_example():
    r = bonus.late_interest(D("7698.02"), date(2023, 12, 31), date(2024, 2, 14))
    assert (r.due_date, r.days_late, r.interest) == (date(2024, 1, 30), 15, D("37.96"))


def test_on_time_and_early():
    assert bonus.late_interest(D("100"), date(2024, 1, 1), date(2024, 1, 31)).days_late == 0
    r = bonus.late_interest(D("100"), date(2024, 1, 1), date(2023, 12, 1))
    assert r.days_late == 0 and r.interest == D("0.00")


def test_one_day_late():
    r = bonus.late_interest(D("365"), date(2024, 1, 1), date(2024, 2, 1))
    assert r.days_late == 1 and r.interest == D("0.12")


def test_rate_change_boundary():
    r = bonus.late_interest(D("365"), date(2024, 5, 31), date(2024, 7, 1))
    assert r.due_date == date(2024, 6, 30) and r.days_late == 1 and r.interest == D("0.09")
    r = bonus.late_interest(D("365"), date(2024, 5, 30), date(2024, 7, 1))
    assert r.days_late == 2 and r.interest == D("0.21")


def test_unpaid_uses_report_date():
    r = bonus.late_interest(D("1006.14"), date(2024, 2, 29), None)   # due 2024-03-30, report 2024-07-20
    assert r.days_late == 112
    expected = D("1006.14") * D("0.12") * 92 / 365, D("1006.14") * D("0.09") * 20 / 365
    assert r.interest == sum((e.quantize(D("0.01"), rounding="ROUND_HALF_UP") for e in expected), D("0"))


def test_first_usable_payment():
    payments = [
        {"id": "x", "paidDate": "2024-13-45"},
        {"id": "unknown", "paidDate": "2024-01-01"},
        {"id": "x", "paidDate": "14/02/2024"},
        {"id": "x", "paidDate": "2024-03-01"},
        "junk", None, {"id": 5, "paidDate": "2024-01-01"}, {"id": "y"},
    ]
    assert bonus.first_usable_payments(payments, {"x", "y"}) == {"x": date(2024, 2, 14)}


def test_last_calendar_day_does_not_crash():
    r = bonus.late_interest(D("100"), date(9999, 12, 31), None)
    assert r.days_late == 0


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("ok  ", t.__name__)   