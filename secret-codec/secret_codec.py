#!/usr/bin/env python3
import argparse
import base64
import getpass
import os
import sys
from typing import Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SALT_LEN = 16
IV_LEN = 12
PBKDF2_ITERS = 250000
KEY_LEN = 32


def derive_key(passphrase: bytes, salt: bytes, iterations: int = PBKDF2_ITERS) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LEN,
        salt=salt,
        iterations=iterations,
    )
    return kdf.derive(passphrase)


def encode_token(salt: bytes, iv: bytes, ciphertext: bytes) -> str:
    return base64.urlsafe_b64encode(salt + iv + ciphertext).decode("utf-8")


def decode_token(token_b64: str) -> tuple[bytes, bytes, bytes]:
    padding = "=" * (-len(token_b64) % 4)
    try:
        full = base64.urlsafe_b64decode(token_b64 + padding)
    except Exception as exc:
        raise ValueError("Invalid token format.") from exc

    minimum_length = SALT_LEN + IV_LEN + 16
    if len(full) < minimum_length:
        raise ValueError("Token is too short or corrupted.")

    salt = full[:SALT_LEN]
    iv = full[SALT_LEN:SALT_LEN + IV_LEN]
    ciphertext = full[SALT_LEN + IV_LEN:]
    return salt, iv, ciphertext


def encrypt_text(plaintext: str, passphrase: str) -> str:
    salt = os.urandom(SALT_LEN)
    iv = os.urandom(IV_LEN)
    key = derive_key(passphrase.encode("utf-8"), salt)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)
    return encode_token(salt, iv, ciphertext)


def decrypt_text(token_b64: str, passphrase: str) -> str:
    salt, iv, ciphertext = decode_token(token_b64.strip())
    key = derive_key(passphrase.encode("utf-8"), salt)
    aesgcm = AESGCM(key)

    try:
        plaintext = aesgcm.decrypt(iv, ciphertext, None)
    except Exception as exc:
        raise ValueError("Decryption failed. Wrong passphrase or corrupted token.") from exc

    try:
        return plaintext.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Decrypted data is not valid UTF-8 text.") from exc


def prompt_secret(prompt_text: str) -> str:
    value = getpass.getpass(prompt_text)
    if value == "":
        raise ValueError("Input cannot be empty.")
    return value


def get_input_value(direct_value: Optional[str], prompt_text: str, hidden: bool = False) -> str:
    if direct_value is not None:
        if direct_value == "":
            raise ValueError("Input cannot be empty.")
        return direct_value

    if hidden:
        return prompt_secret(prompt_text)

    value = input(prompt_text).strip()
    if value == "":
        raise ValueError("Input cannot be empty.")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Encrypt and decrypt text using AES-GCM with a PBKDF2-derived key."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    encrypt_parser = subparsers.add_parser("encrypt", help="Encrypt plaintext into a token")
    encrypt_parser.add_argument("--text", help="Plaintext to encrypt")
    encrypt_parser.add_argument("--passphrase", help="Master passphrase")

    decrypt_parser = subparsers.add_parser("decrypt", help="Decrypt a token into plaintext")
    decrypt_parser.add_argument("--token", help="Token to decrypt")
    decrypt_parser.add_argument("--passphrase", help="Master passphrase")

    return parser


def main() -> int:
    try:
        parser = build_parser()
        args = parser.parse_args()

        if args.command == "encrypt":
            plaintext = get_input_value(args.text, "Enter text to encrypt: ", hidden=True)
            passphrase = get_input_value(args.passphrase, "Enter your master passphrase: ", hidden=True)
            token = encrypt_text(plaintext, passphrase)
            print(token)
            return 0

        if args.command == "decrypt":
            token = get_input_value(args.token, "Paste token: ")
            passphrase = get_input_value(args.passphrase, "Enter your master passphrase: ", hidden=True)
            plaintext = decrypt_text(token, passphrase)
            print(plaintext)
            return 0

        parser.print_help()
        return 1

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())