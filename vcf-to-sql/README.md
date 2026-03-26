# vcf-to-sql

Convert `.vcf` contact files into SQL `INSERT` statements.

## Usage

```bash
python vcf_to_sql.py contacts.vcf contacts.sql
```

## Notes

- The script extracts contact names, phone numbers, emails, and addresses
- The generated SQL assumes a table with these columns:
  - `name`
  - `phone`
  - `email`
  - `address`
  - `created_at`
  - `updated_at`
