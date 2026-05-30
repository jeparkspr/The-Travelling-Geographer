FROM nginx:alpine

# Install openssl for self-signed certs, certbot for Let's Encrypt,
# and avahi + dbus for mDNS advertisement of travel.local
RUN apk add --no-cache openssl certbot avahi dbus

# Configure Avahi for mDNS
COPY avahi-daemon.conf /etc/avahi/avahi-daemon.conf

# Copy nginx config and entrypoint
COPY nginx.conf /etc/nginx/nginx.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 80 443

ENTRYPOINT ["/entrypoint.sh"]
