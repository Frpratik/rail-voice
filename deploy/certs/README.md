# TLS certificates for Nginx

Place `fullchain.pem` and `privkey.pem` here for HTTPS.

## Self-signed (local smoke only)

```bash
openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
  -keyout deploy/certs/privkey.pem \
  -out deploy/certs/fullchain.pem \
  -subj "/CN=localhost"
```

## Let's Encrypt (production)

Use Certbot on the host or a companion container, then mount the live certs into this directory (or update the nginx volume paths).
