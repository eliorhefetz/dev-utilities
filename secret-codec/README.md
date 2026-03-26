# secret-codec

Encrypt and decrypt text using AES-GCM with a PBKDF2-derived key.

## Features

- Encrypt plaintext into a URL-safe token
- Decrypt a token back into plaintext
- Use AES-GCM for authenticated encryption
- Derive the encryption key from a master passphrase with PBKDF2-HMAC-SHA256
- Support both interactive mode and direct command-line arguments


## Usage

Encrypt interactively:

```bash
python secret_codec.py encrypt
```

Decrypt interactively:

```bash
python secret_codec.py decrypt
```

Encrypt without prompts:

```bash
python secret_codec.py encrypt --text "my-secret" --passphrase "my-master-passphrase"
```

Decrypt without prompts:

```bash
python secret_codec.py decrypt --token "TOKEN_HERE" --passphrase "my-master-passphrase"
```

## Notes

- The tool outputs a single URL-safe Base64 token
- The token contains the salt, IV, and ciphertext
- The same master passphrase is required for decryption
- If the passphrase is wrong or the token is corrupted, decryption will fail
