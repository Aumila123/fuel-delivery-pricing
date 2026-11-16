import contextlib
import io
import os
import tempfile
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import main
from pricing import calculate_delivery
from validation import Shipment


def test_invalid_shipments_input_stops_without_overwriting_output():
    with tempfile.TemporaryDirectory() as directory:
        shipments_path = os.path.join(directory, "shipments.json")
        output_dir = os.path.join(directory, "output")
        os.makedirs(output_dir)
        output_path = os.path.join(output_dir, "errors.csv")
        with open(output_path, "w", encoding="utf-8") as file:
            file.write("existing")

        for contents in ('{"id":', '{"not":"an array"}',
                         '[{"id":"one","id":"two"}]', '[NaN]'):
            with open(shipments_path, "w", encoding="utf-8") as file:
                file.write(contents)
            errors = io.StringIO()
            with patch.object(main, "SHIPMENTS_FILE", shipments_path), \
                    patch.object(main, "OUTPUT_DIR", output_dir), \
                    contextlib.redirect_stderr(errors):
                main.main()

            with open(output_path, encoding="utf-8") as file:
                assert file.read() == "existing"
            assert "processing stopped" in errors.getvalue()


def test_invalid_payments_input_skips_bonus_without_overwriting_output():
    shipment = Shipment("123e4567-e89b-12d3-a456-426614174000", "DIESEL",
                        "PRIVATE", date(2024, 1, 1), Decimal("1000"),
                        Decimal("0"), Decimal("1"))
    price = calculate_delivery(shipment.type, shipment.client, shipment.date,
                               shipment.volume, shipment.distance, shipment.base_price)

    with tempfile.TemporaryDirectory() as directory:
        payments_path = os.path.join(directory, "payments.json")
        output_dir = os.path.join(directory, "output")
        os.makedirs(output_dir)
        output_path = os.path.join(output_dir, "bonus2.csv")
        with open(output_path, "w", encoding="utf-8") as file:
            file.write("existing")

        for contents in ('{"id":', '{"not":"an array"}',
                         '[{"id":"one","id":"two"}]', '[NaN]'):
            with open(payments_path, "w", encoding="utf-8") as file:
                file.write(contents)
            errors = io.StringIO()
            with patch.object(main, "PAYMENTS_FILE", payments_path), \
                    patch.object(main, "OUTPUT_DIR", output_dir), \
                    contextlib.redirect_stderr(errors):
                main.run_bonus2([(shipment, price)])

            with open(output_path, encoding="utf-8") as file:
                assert file.read() == "existing"
            assert "Bonus 2 skipped" in errors.getvalue()


def test_missing_payments_means_unpaid():
    shipment = Shipment("123e4567-e89b-12d3-a456-426614174000", "DIESEL",
                        "PRIVATE", date(2024, 1, 1), Decimal("1000"),
                        Decimal("0"), Decimal("1"))
    price = calculate_delivery(shipment.type, shipment.client, shipment.date,
                               shipment.volume, shipment.distance, shipment.base_price)

    with tempfile.TemporaryDirectory() as directory:
        output_dir = os.path.join(directory, "output")
        with patch.object(main, "PAYMENTS_FILE", os.path.join(directory, "missing.json")), \
                patch.object(main, "OUTPUT_DIR", output_dir):
            main.run_bonus2([(shipment, price)])

        with open(os.path.join(output_dir, "bonus2.csv"), encoding="utf-8") as file:
            assert file.read().splitlines()[-1].split(",")[2] == "171"


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print("ok  ", test.__name__)
