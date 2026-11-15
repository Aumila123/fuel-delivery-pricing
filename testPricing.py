from datetime import date
from decimal import Decimal as D

from pricing import calculate_delivery, round2


def test_round_half_up():
    assert round2(D("0.125")) == D("0.13")
    assert round2(D("2.675")) == D("2.68")


def test_discount_not_rounded_separately():
    r = calculate_delivery("GASOLINE", "PRIVATE", date(2024, 4, 3),
                           D("6200"), D("63.7"), D("0.8775"))
    assert r.net_fuel_price == D("5168.48")


def test_pdf_example_task1():
    r = calculate_delivery("LPG", "PRIVATE", date(2024, 7, 4),
                           D("12000"), D("90"), D("0.51"))
    assert r.net_fuel_price == D("5814.00")
    assert r.logistics_cost == D("162.00")
    assert r.vat == D("1871.28")
    assert r.total_tax == D("4031.28")
    assert r.grand_total == D("10007.28")


def test_pdf_example_task2():
    r = calculate_delivery("LPG", "PRIVATE", date(2024, 7, 4),
                           D("12000"), D("90"), D("0.51"),
                           custom_private_vat=D("0.25"),
                           custom_gasoline_excise=D("0.52"))
    assert r.total_tax == D("4194.00")
    assert r.grand_total == D("10170.00")


def test_bonus2_example_grand_total():
    r = calculate_delivery("DIESEL", "PRIVATE", date(2023, 12, 31),
                           D("5000"), D("90"), D("0.91"))
    assert r.grand_total == D("7698.02")


def test_thresholds():
    def net(v):
        return calculate_delivery("DIESEL", "EXEMPT", date(2024, 1, 1),
                                  D(v), D("0"), D("1")).net_fuel_price
    assert net("5000") == D("5000.00")
    assert net("5001") == D("4750.95")
    assert net("20000") == D("19000.00")
    assert net("20001") == D("18000.90")


def test_small_load_fee_and_exempt():
    r = calculate_delivery("DIESEL", "EXEMPT", date(2024, 4, 10),
                           D("999"), D("30"), D("0.9"))
    assert r.logistics_cost == D("204.00")
    assert r.vat == D("0.00")
    r = calculate_delivery("DIESEL", "EXEMPT", date(2024, 4, 10),
                           D("1000"), D("30"), D("0.9"))
    assert r.logistics_cost == D("54.00")


def test_vat_change_date():
    old = calculate_delivery("DIESEL", "PRIVATE", date(2023, 12, 31),
                             D("5000"), D("0"), D("1"))
    new = calculate_delivery("DIESEL", "PRIVATE", date(2024, 1, 1),
                             D("5000"), D("0"), D("1"))
    assert old.vat == D("1396.50")
    assert new.vat == D("1529.50")


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("ok  ", t.__name__)