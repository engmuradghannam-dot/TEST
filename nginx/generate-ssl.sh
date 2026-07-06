#!/bin/bash
# Generate self-signed SSL certificate for development
# For production, replace with real certificates from Let's Encrypt or your CA

set -e

SSL_DIR="$(dirname "$0")"
KEY_FILE="$SSL_DIR/key.pem"
CERT_FILE="$SSL_DIR/cert.pem"

if [ -f "$KEY_FILE" ] && [ -f "$CERT_FILE" ]; then
    echo "SSL certificates already exist."
    exit 0
fi

echo "Generating self-signed SSL certificate..."

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$KEY_FILE" \
    -out "$CERT_FILE" \
    -subj "/C=SA/ST=Riyadh/L=Riyadh/O=Nexus Framework/OU=Dev/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,DNS:*.localhost,IP:127.0.0.1"

echo "SSL certificates generated:"
echo "  Key: $KEY_FILE"
echo "  Cert: $CERT_FILE"
echo ""
echo "For production, replace these with certificates from:"
echo "  - Let's Encrypt (free)"
echo "  - Your Certificate Authority"
echo "  - Cloudflare Origin CA"
