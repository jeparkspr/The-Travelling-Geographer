#!/bin/sh
set -e

SSL_DIR="/etc/nginx/ssl"
CERTBOT_DIR="/var/www/certbot"
TLS_MODE="${TLS_MODE:-self-signed}"
DOMAIN="${DOMAIN:-localhost}"

mkdir -p "$SSL_DIR" "$CERTBOT_DIR"

echo "=== TLS Mode: $TLS_MODE ==="

if [ "$TLS_MODE" = "letsencrypt" ]; then
    # Let's Encrypt mode
    if [ "$DOMAIN" = "localhost" ]; then
        echo "ERROR: DOMAIN must be set to a real domain for Let's Encrypt"
        exit 1
    fi

    CERT_PATH="/etc/letsencrypt/live/$DOMAIN"

    if [ ! -f "$CERT_PATH/fullchain.pem" ]; then
        echo "Obtaining Let's Encrypt certificate for $DOMAIN..."

        # Generate a temporary self-signed cert so nginx can start for the ACME challenge
        openssl req -x509 -nodes -days 1 \
            -newkey rsa:2048 \
            -keyout "$SSL_DIR/key.pem" \
            -out "$SSL_DIR/cert.pem" \
            -subj "/CN=temporary" 2>/dev/null

        # Start nginx in background for ACME challenge
        nginx &
        NGINX_PID=$!
        sleep 2

        # Request the certificate
        certbot certonly --webroot \
            -w "$CERTBOT_DIR" \
            -d "$DOMAIN" \
            --email "${CERTBOT_EMAIL:-admin@$DOMAIN}" \
            --agree-tos \
            --no-eff-email \
            --non-interactive

        # Stop background nginx
        kill $NGINX_PID 2>/dev/null || true
        wait $NGINX_PID 2>/dev/null || true
    fi

    # Link Let's Encrypt certs
    ln -sf "$CERT_PATH/fullchain.pem" "$SSL_DIR/cert.pem"
    ln -sf "$CERT_PATH/privkey.pem" "$SSL_DIR/key.pem"

    # Set up auto-renewal cron (runs twice daily)
    echo "0 */12 * * * certbot renew --quiet --deploy-hook 'nginx -s reload'" | crontab -
    crond

    echo "Let's Encrypt certificate ready for $DOMAIN"

else
    # Self-signed mode (default)
    if [ ! -f "$SSL_DIR/cert.pem" ] || [ ! -f "$SSL_DIR/key.pem" ]; then
        echo "Generating self-signed certificate for $DOMAIN..."
        openssl req -x509 -nodes -days 3650 \
            -newkey rsa:2048 \
            -keyout "$SSL_DIR/key.pem" \
            -out "$SSL_DIR/cert.pem" \
            -subj "/CN=$DOMAIN/O=The Travelling Geographer/C=US" \
            -addext "subjectAltName=DNS:$DOMAIN,DNS:localhost,IP:127.0.0.1" \
            2>/dev/null
        echo "Self-signed certificate generated (valid for 10 years)"
    else
        echo "Using existing SSL certificates"
    fi
fi

# Start dbus and avahi for mDNS advertisement (travel.local)
echo "Starting mDNS (avahi)..."
mkdir -p /run/dbus
rm -f /run/dbus/pid
dbus-daemon --system --nopidfile 2>/dev/null
avahi-daemon --daemonize --no-chroot 2>/dev/null
echo "mDNS advertising $(hostname).local"

echo "Starting nginx..."
exec nginx -g "daemon off;"
