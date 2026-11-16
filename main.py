import csv
import json
import os
import sys
import re
from decimal import Decimal, localcontext

import bonus
import pricing
import validation

NAME = "Austeja_Milaseviciute"
SHIPMENTS_FILE = "shipments.json"
PAYMENTS_FILE = "payments.json"
OUTPUT_DIR = "output"
PRICE_HEADER = ["ShipmentID", "NetFuelPrice", "LogisticsCost", "TotalTax", "GrandTotal"]

PROMPT_VAT = "Enter custom VAT rate for Private clients (%): "
PROMPT_EXCISE = "Enter custom Excise rate for Gasoline: "
PROMPT_START = "Enter Start Date (YYYY-MM-DD or DD/MM/YYYY): "
PROMPT_END = "Enter End Date (YYYY-MM-DD or DD/MM/YYYY): "

_NUMBER = re.compile(r"\+?(\d+(\.\d*)?|\.\d+)", re.ASCII)

def load_json(path):
    def reject_duplicate_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON object key: {key!r}")
            result[key] = value
        return result

    def reject_nonstandard_constant(value):
        raise ValueError(f"invalid JSON numeric constant: {value}")

    with open(path, encoding="utf-8-sig") as f:
        return json.load(f, parse_float=Decimal, object_pairs_hook=reject_duplicate_keys,
                         parse_constant=reject_nonstandard_constant)


def write_csv(filename, header, rows):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow([NAME])
        writer.writerow(header)
        writer.writerows(rows)


def money(value):
    return f"{value:.2f}"


def split_records(records):
    seen_ids = set()
    valid, errors = [], []
    for record in records:
        result = validation.validate_record(record, seen_ids)
        if result.error:
            errors.append((result.shipment_id, result.error))
        else:
            valid.append(result.shipment)
    return valid, errors


def price_all(shipments, custom_private_vat=None, custom_gasoline_excise=None):
    return [
        (s, pricing.calculate_delivery(
            s.type, s.client, s.date, s.volume, s.distance, s.base_price,
            custom_private_vat, custom_gasoline_excise))
        for s in shipments
    ]


def price_rows(priced):
    return [[s.id, money(p.net_fuel_price), money(p.logistics_cost),
             money(p.total_tax), money(p.grand_total)] for s, p in priced]

def parse_non_negative(text):
    text = text.strip()
    if not _NUMBER.fullmatch(text):
        return None
    return Decimal(text)

def ask_decimal(prompt):
    while True:
        value = parse_non_negative(input(prompt))
        if value is not None:
            return value
        print("Error: enter a number that is 0 or more.")

def run_task2(shipments):
    try:
        vat_percent = ask_decimal(PROMPT_VAT)
        gasoline_excise = ask_decimal(PROMPT_EXCISE)
    except EOFError:
        print("Input ended, Task 2 skipped.", file=sys.stderr)
        return None
    with localcontext() as context:
        context.prec = pricing.decimal_precision(vat_percent, extra=4)
        custom_vat_rate = vat_percent / 100
    priced = price_all(shipments, custom_vat_rate, gasoline_excise)
    write_csv("task2.csv", PRICE_HEADER, price_rows(priced))
    return priced

def ask_date(prompt, not_before=None):
    """Asks until the answer is a real date (and not before not_before).
    Raises EOFError if the input ends."""
    while True:
        value = validation.parse_date(input(prompt).strip())
        if value is None:
            print("Error: invalid date. Use YYYY-MM-DD or DD/MM/YYYY.")
        elif not_before is not None and value < not_before:
            print("Error: End Date must not be before Start Date.")
        else:
            return value

def run_bonus1(priced):
    """Uses the Task 2 results. Asks for the date range, writes bonus1.csv."""
    try:
        start = ask_date(PROMPT_START)
        end = ask_date(PROMPT_END, not_before=start)   # only the End Date is asked again
    except EOFError:
        print("Input ended, Bonus 1 skipped.", file=sys.stderr)
        return
    count, best_id, total_vat = bonus.summarize_range(priced, start, end)
    write_csv("bonus1.csv", ["ShipmentCount", "MostExpensiveID", "TotalVAT"],
              [[str(count), best_id, money(total_vat)]])

def run_bonus2(priced):
    try:
        payments = load_json(PAYMENTS_FILE)
    except FileNotFoundError:
        payments = []
    except (OSError, ValueError, RecursionError) as error:
        print(f"Cannot read {PAYMENTS_FILE}: {error}; Bonus 2 skipped.", file=sys.stderr)
        return
    if not isinstance(payments, list):
        print(f"Invalid {PAYMENTS_FILE}: expected a JSON array; Bonus 2 skipped.",
              file=sys.stderr)
        return
    paid_dates = bonus.first_usable_payments(payments, {s.id for s, _ in priced})
    rows = []
    for shipment, price in priced:
        late = bonus.late_interest(price.grand_total, shipment.date, paid_dates.get(shipment.id))
        rows.append([shipment.id, late.due_date.isoformat(), str(late.days_late),
                     money(late.interest)])
    write_csv("bonus2.csv", ["ShipmentID", "DueDate", "DaysLate", "LateInterest"], rows)

def main():
    try:
        records = load_json(SHIPMENTS_FILE)
    except (OSError, ValueError, RecursionError) as error:
        print(f"Cannot read {SHIPMENTS_FILE}: {error}; processing stopped.",
              file=sys.stderr)
        return
    if not isinstance(records, list):
        print(f"Invalid {SHIPMENTS_FILE}: expected a JSON array; processing stopped.",
              file=sys.stderr)
        return
    shipments, errors = split_records(records)

    write_csv("errors.csv", ["ShipmentID", "ErrorCode"], errors)

    # Task 1
    standard = price_all(shipments)
    write_csv("task1.csv", PRICE_HEADER, price_rows(standard))

    # Task 2
    custom = run_task2(shipments)

    # Bonus 1
    if custom is not None:
        run_bonus1(custom)

    # Bonus 2
    run_bonus2(standard)

if __name__ == "__main__":
    main()