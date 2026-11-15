import csv
import json
import os
import sys
import re
from decimal import Decimal

import pricing
import validation

NAME = "Austeja_Milaseviciute"
SHIPMENTS_FILE = "shipments.json"
OUTPUT_DIR = "output"
PRICE_HEADER = ["ShipmentID", "NetFuelPrice", "LogisticsCost", "TotalTax", "GrandTotal"]

PROMPT_VAT = "Enter custom VAT rate for Private clients (%): "
PROMPT_EXCISE = "Enter custom Excise rate for Gasoline: "

_NUMBER = re.compile(r"\+?(\d+(\.\d*)?|\.\d+)", re.ASCII)

def load_json(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f, parse_float=Decimal)
    except (OSError, ValueError) as error:
        print(f"Cannot read {path}: {error}", file=sys.stderr)
        return None


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
    """-> list of (shipment, DeliveryPrice), same order as shipments."""
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
    priced = price_all(shipments, vat_percent / 100, gasoline_excise)  
    write_csv("task2.csv", PRICE_HEADER, price_rows(priced))
    return priced

def main():
    records = load_json(SHIPMENTS_FILE)
    if not isinstance(records, list):
        records = []
    shipments, errors = split_records(records)

    write_csv("errors.csv", ["ShipmentID", "ErrorCode"], errors)

    # Task 1
    standard = price_all(shipments)
    write_csv("task1.csv", PRICE_HEADER, price_rows(standard))

    # Task 2
    run_task2(shipments)

if __name__ == "__main__":
    main()