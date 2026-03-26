#!/usr/bin/env python3
import argparse
import csv
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert VCF contacts into CSV rows."
    )
    parser.add_argument("input_file", help="Path to the input VCF file")
    parser.add_argument("output_file", help="Path to the output CSV file")
    parser.add_argument(
        "--created-column",
        default="created_at",
        help="Created-at column name (default: created_at)",
    )
    parser.add_argument(
        "--updated-column",
        default="updated_at",
        help="Updated-at column name (default: updated_at)",
    )
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Date value to use for created and updated columns (default: today in YYYY-MM-DD format)",
    )
    return parser.parse_args()


def validate_csv_column_name(value: str, field_name: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"Invalid {field_name}: {value!r}")
    return value


def read_text_file(file_path: Path) -> str:
    try:
        return file_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Input file not found: {file_path}") from exc
    except OSError as exc:
        raise OSError(f"Failed to read input file {file_path}: {exc}") from exc


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def extract_first_match(pattern: str, text: str) -> str:
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        return ""
    return normalize_whitespace(match.group(1))


def extract_name_from_n(card: str) -> str:
    raw_n = extract_first_match(r"^N:(.+)$", card)
    if not raw_n:
        return ""

    parts = [normalize_whitespace(part) for part in raw_n.split(";")]
    parts = [part for part in parts if part]
    return normalize_whitespace(" ".join(parts))


def normalize_phone_number(value: str) -> str:
    value = normalize_whitespace(value)
    value = re.sub(r"[^\d+]", "", value)

    if value.startswith("+972"):
        value = "0" + value[4:]
    elif value.startswith("972"):
        value = "0" + value[3:]

    value = re.sub(r"\D", "", value)

    if len(value) == 10 and value.startswith("0"):
        return value

    return ""


def is_valid_email(value: str) -> bool:
    value = normalize_whitespace(value)
    if value == "":
        return False
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value))


def is_reasonable_name(value: str) -> bool:
    value = normalize_whitespace(value)
    if not value:
        return False

    compact = re.sub(r"\s+", "", value)
    if compact.isdigit():
        return False

    letter_count = len(re.findall(r"[A-Za-zא-ת]", value))
    digit_count = len(re.findall(r"\d", value))

    if letter_count < 2:
        return False

    if digit_count > letter_count:
        return False

    return True


def extract_contact(card: str, fallback_index: int) -> Optional[Dict[str, str]]:
    raw_phone = extract_first_match(r"^(?:item\d+\.)?TEL[^:]*:(.+)$", card)
    phone = normalize_phone_number(raw_phone)

    if phone == "":
        return None

    name = extract_first_match(r"^FN:(.+)$", card)
    if not is_reasonable_name(name):
        name = extract_name_from_n(card)

    if not is_reasonable_name(name):
        name = f"Unknown Contact {fallback_index}"

    raw_email = extract_first_match(r"^(?:item\d+\.)?EMAIL[^:]*:(.+)$", card)
    email = normalize_whitespace(raw_email) if is_valid_email(raw_email) else ""

    raw_address = extract_first_match(r"^(?:item\d+\.)?ADR[^:]*:(.+)$", card)
    address = normalize_whitespace(raw_address)

    return {
        "name": name,
        "phone": phone,
        "email": email,
        "address": address,
    }


def parse_vcf_contacts(vcf_content: str) -> List[Dict[str, str]]:
    cards = vcf_content.split("END:VCARD")
    contacts: List[Dict[str, str]] = []
    fallback_index = 1

    for card in cards:
        contact = extract_contact(card, fallback_index)
        if contact is not None:
            contacts.append(contact)
            if contact["name"].startswith("Unknown Contact "):
                fallback_index += 1

    return contacts


def write_csv_file(
    output_path: Path,
    contacts: List[Dict[str, str]],
    created_column: str,
    updated_column: str,
    date_value: str,
) -> None:
    fieldnames = [
        "name",
        "phone",
        "email",
        "address",
        created_column,
        updated_column,
    ]

    try:
        with output_path.open("w", encoding="utf-8-sig", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            for contact in contacts:
                writer.writerow(
                    {
                        "name": contact["name"],
                        "phone": contact["phone"],
                        "email": contact["email"],
                        "address": contact["address"],
                        created_column: date_value,
                        updated_column: date_value,
                    }
                )
    except OSError as exc:
        raise OSError(f"Failed to write output file {output_path}: {exc}") from exc


def main() -> int:
    try:
        args = parse_arguments()

        input_path = Path(args.input_file)
        output_path = Path(args.output_file)

        created_column = validate_csv_column_name(args.created_column, "created column")
        updated_column = validate_csv_column_name(args.updated_column, "updated column")

        vcf_content = read_text_file(input_path)
        contacts = parse_vcf_contacts(vcf_content)

        write_csv_file(
            output_path=output_path,
            contacts=contacts,
            created_column=created_column,
            updated_column=updated_column,
            date_value=args.date,
        )

        print(f"Created CSV file: {output_path}")
        print(f"Processed contacts: {len(contacts)}")
        return 0

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())