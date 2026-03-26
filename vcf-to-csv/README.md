# vcf-to-csv

Convert `.vcf` contact files into CSV rows.

## Features

- Parse contact names, phone numbers, emails, and addresses
- Keep only contacts with a valid Israeli phone number
- Use automatic fallback names for contacts without a reasonable name
- Support custom `created_at` and `updated_at` column names
- Support a custom date value for generated records

## Usage

```bash
python vcf_to_csv.py contacts.vcf contacts.csv
```

## Custom timestamp columns

```bash
python vcf_to_csv.py contacts.vcf contacts.csv --created-column created_at --updated-column updated_at
```

## Custom date

```bash
python vcf_to_csv.py contacts.vcf contacts.csv --date 2026-03-27
```

## Output columns

The generated CSV contains these columns:

- `name`
- `phone`
- `email`
- `address`
- `created_at`
- `updated_at`

## Notes

- The script accepts Israeli phone numbers in local format such as `050...`, `052...`, `058...`
- The script also normalizes Israeli international numbers such as `+972...` and `972...` into local format
- If a contact does not have a reasonable name, the script assigns a fallback name like `Unknown Contact 1`
- If an email is missing or invalid, the script leaves it empty
- Contacts without a valid phone number are skipped
