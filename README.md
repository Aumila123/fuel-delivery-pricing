# Fuel Delivery Pricing Task

This project reads shipment and payment data from JSON files, validates the records, calculates delivery invoices, and writes the results to CSV files in an `output/` directory.

## Running the program

To run it without typing:

PowerShell:
"25","0.52","2024-01-01","2024-01-31" | python main.py

Linux / macOS:
printf "25\n0.52\n2024-01-01\n2024-01-31\n" | python main.py

From the project folder, run:

```bash
python main.py
```

If Task 2 is enabled, the program will prompt for input in this order:

```text
Enter custom VAT rate for Private clients (%):
Enter custom Excise rate for Gasoline:
```

Then for Bonus 1:

```text
Enter Start Date (YYYY-MM-DD or DD/MM/YYYY):
Enter End Date (YYYY-MM-DD or DD/MM/YYYY):
```

The task includes:

- Task 1: standard pricing for all valid deliveries
- Task 2: pricing with custom VAT and gasoline excise values
- Bonus 1: summary for a selected date range
- Bonus 2: late payment interest calculation

## Project structure

- `main.py` — main program flow, file reading, task orchestration, and CSV output
- `pricing.py` — pricing logic and financial calculations
- `validation.py` — record validation and error code handling
- `bonus.py` — bonus calculations for date ranges and late payments
- `config.py` — constants and configurable business rules
- `shipments.json` — list of delivery records
- `payments.json` — payment records used by Bonus 2
- `output/` — generated CSV files

## How the program works

The program reads `shipments.json` from the current working directory.

Each shipment record must contain:

- `id`
- `type`
- `client`
- `date`
- `volume`
- `distance`
- `basePrice`

Records with invalid values are rejected and written to `output/errors.csv` using one of the required error codes:

- `MISSING_FIELD`
- `UNKNOWN_TYPE`
- `UNKNOWN_CLIENT`
- `INVALID_DATE`
- `INVALID_VALUE`
- `DUPLICATE_ID`

Valid shipments are processed and included in the pricing outputs.

## Pricing rules

The calculation follows the task specification:

- Net fuel price is calculated as:
  `volume * basePrice * (1 - discount_rate)`
- Discount rate depends on volume thresholds
- Logistics cost is based on distance and a small-load fee when applicable
- Excise depends on fuel type
- VAT depends on client type and date:
  - `EXEMPT` = 0%
  - `PRIVATE` before `2024-01-01` = 21%
  - `PRIVATE` from `2024-01-01` = 23%
- All monetary calculations use `Decimal` and rounding is handled according to the task rules

## Task flow

When the program runs:

1. It reads and validates `shipments.json`
2. It writes `output/errors.csv`
3. It creates `output/task1.csv`
4. It asks for the custom VAT percentage and custom gasoline excise rate
5. It creates `output/task2.csv`
6. If Task 2 is completed, it asks for a date range and writes `output/bonus1.csv`
7. It calculates late-payment interest using `payments.json` and writes `output/bonus2.csv`

## Output files

The generated files are written to the `output/` folder.

### `output/task1.csv`
Contains valid shipment prices for the standard scenario.

### `output/task2.csv`
Contains valid shipment prices using custom VAT and gasoline excise values.

### `output/bonus1.csv`
Contains:
- total shipments in the selected date range
- ID of the most expensive shipment
- total VAT for that range

### `output/bonus2.csv`
Contains:
- shipment ID
- due date
- days late
- late interest

### `output/errors.csv`
Contains rejected shipment records and their error codes.

## Notes

- The program writes all output files to the `output/` directory.
- It preserves input order for valid shipments.
- It ignores invalid records in price calculations.
- Money is handled with `Decimal`, not floating point numbers.

## AI tool used

I used GitHub Copilot in VS Code for:

- reviewing the task requirements and clarifying edge cases
- helping implement the validation logic
- checking calculations and rounding behavior
- validating the final project against the provided tests and examples
This tool was used to accelerate code review, debugging, and correctness checks while staying within the task requirements.

I used Claude (Anthropic) as an assistant in this project:

- To break the task into steps and plan the file structure.
- To help find the cause of failing tests.
