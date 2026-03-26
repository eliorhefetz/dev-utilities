#!/usr/bin/env python3
import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert VCF contacts into SQL INSERT statements."
    )
    parser.add_argument("input_file", help="Path to the input VCF file")
    parser.add_argument("output_file", help="Path to the output SQL file")
    parser.add_argument(
        "--table",
        default="clients",
        help="Target SQL table name (default: clients)",
    )
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


def validate_sql_identifier(value: str, field_name: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise ValueError(f"Invalid {field_name}: {value!r}")
    return value


def read_text_file(file_path: Path) -> str:
    try:
        return file_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Input file not found: {file_path}") from exc
    except OSError as exc:
        raise OSError(f"Failed to read input file {file_path}: {exc}") from exc


def write_text_file(file_path: Path, content: str) -> None:
    try:
        file_path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise OSError(f"Failed to write output file {file_path}: {exc}") from exc


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def escape_sql_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "''")


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


def build_insert_statement(
    contacts: List[Dict[str, str]],
    table_name: str,
    created_column: str,
    updated_column: str,
    date_value: str,
) -> str:
    if not contacts:
        return "-- No valid contacts found.\n"

    lines = [
        f"INSERT INTO {table_name} "
        f"(name, phone, email, address, {created_column}, {updated_column}) VALUES"
    ]

    for contact in contacts:
        escaped_name = escape_sql_string(contact["name"])
        escaped_phone = escape_sql_string(contact["phone"])
        escaped_email = escape_sql_string(contact["email"])
        escaped_address = escape_sql_string(contact["address"])
        escaped_date = escape_sql_string(date_value)

        lines.append(
            f"('{escaped_name}', '{escaped_phone}', '{escaped_email}', "
            f"'{escaped_address}', '{escaped_date}', '{escaped_date}'),"
        )

    lines[-1] = lines[-1][:-1] + ";"
    return "\n".join(lines) + "\n"


def main() -> int:
    try:
        args = parse_arguments()

        input_path = Path(args.input_file)
        output_path = Path(args.output_file)

        table_name = validate_sql_identifier(args.table, "table name")
        created_column = validate_sql_identifier(args.created_column, "created column")
        updated_column = validate_sql_identifier(args.updated_column, "updated column")

        vcf_content = read_text_file(input_path)
        contacts = parse_vcf_contacts(vcf_content)

        sql_output = build_insert_statement(
            contacts=contacts,
            table_name=table_name,
            created_column=created_column,
            updated_column=updated_column,
            date_value=args.date,
        )

        write_text_file(output_path, sql_output)

        print(f"Created SQL file: {output_path}")
        print(f"Processed contacts: {len(contacts)}")
        return 0

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())