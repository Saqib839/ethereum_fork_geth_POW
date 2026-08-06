# Nginx Setup Guide — `rpc.markettrackerx.com`

Based on your Route 53 record:

| Field | Value |
|---|---|
| Record name | `rpc.markettrackerx.com` |
| Type | A |
| Value (server public IP) | `45.249.8.94` |
| TTL | 300 |
| Routing policy | Simple |

This guide assumes the DNS `A` record above is already pointing to your server (`45.249.8.94`), and that your RPC service is running locally on the server (e.g. `127.0.0.1:8545`). Adjust the `proxy_pass` port if your actual RPC service listens elsewhere.

---

## 1. Prerequisites

- Nginx installed on the server at `45.249.8.94`
- DNS propagated (`dig rpc.markettrackerx.com` should return `45.249.8.94`)
- Your RPC backend already running and listening locally (confirm with `curl http://127.0.0.1:8545` or `sudo ss -tlnp | grep 8545`)

---

## 2. Create the Nginx server block

Create a new config file:

```bash
sudo nano /etc/nginx/sites-available/rpc.markettrackerx.com
```

Paste the following:

```nginx
# HTTP - will redirect to HTTPS once SSL is issued (see step 4)
server {
    listen 80;
    listen [::]:80;
    server_name rpc.markettrackerx.com;

    # Used by certbot for the ACME HTTP-01 challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS - main RPC reverse proxy
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
    server_name rpc.markettrackerx.com;

    # SSL certs (populated by certbot in step 4)
    ssl_certificate     /etc/letsencrypt/live/rpc.markettrackerx.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/rpc.markettrackerx.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Basic hardening
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Optional: cap request body size (JSON-RPC payloads are usually small)
    client_max_body_size 2m;

    # Optional: basic rate limiting (uncomment to enable, define zone below)
    # limit_req zone=rpc_limit burst=20 nodelay;

    location / {
        proxy_pass http://127.0.0.1:8545;   # <-- change to your actual RPC port
        proxy_http_version 1.1;

        # WebSocket support (needed if your RPC also serves eth_subscribe / WS)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_read_timeout 300s;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
    }
}
```

> **Note:** If your RPC node exposes HTTP and WebSocket on *different* ports (common for Geth/Erigon-style nodes, e.g. `8545` for HTTP and `8546` for WS), split this into two `location` blocks or two subdomains (`rpc.` and `ws.`) instead of proxying both through one port.

Optional rate-limit zone (add near the top of `/etc/nginx/nginx.conf`, inside the `http {}` block, if you enabled `limit_req` above):

```nginx
limit_req_zone $binary_remote_addr zone=rpc_limit:10m rate=10r/s;
```

---

## 3. Enable the site

```bash
sudo ln -s /etc/nginx/sites-available/rpc.markettrackerx.com /etc/nginx/sites-enabled/
sudo nginx -t          # test config syntax
sudo systemctl reload nginx
```

---

## 4. Issue an SSL certificate (Let's Encrypt / Certbot)

```bash
sudo apt install certbot python3-certbot-nginx -y   # if not already installed
sudo certbot --nginx -d rpc.markettrackerx.com
```

Certbot will automatically detect the server block, obtain the cert, and update the config to reference it (matching the `ssl_certificate` paths already in step 2). Confirm auto-renewal is scheduled:

```bash
sudo systemctl status certbot.timer
sudo certbot renew --dry-run
```

---

## 5. Verify

```bash
curl -X POST https://rpc.markettrackerx.com \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

You should get a JSON-RPC response back through HTTPS. If it hangs or errors:

```bash
sudo tail -f /var/log/nginx/error.log
sudo systemctl status nginx
```

---

## 6. Troubleshooting notes (from actual setup)

These issues came up during real setup on Ubuntu with an older Nginx build — keeping them here in case you rebuild this later.

### "unknown directive http2"
Older Nginx (pre-1.25.1) doesn't support the standalone `http2 on;` directive — it must be a flag on the `listen` line instead.

**Fix:** change
```nginx
listen 443 ssl;
listen [::]:443 ssl;
http2 on;
```
to
```nginx
listen 443 ssl http2;
listen [::]:443 ssl http2;
```

One-shot fix via `sed`:
```bash
sudo sed -i '/listen 443 ssl;/c\    listen 443 ssl http2;' /etc/nginx/sites-available/rpc.markettrackerx.com
sudo sed -i '/listen \[::\]:443 ssl;/c\    listen [::]:443 ssl http2;' /etc/nginx/sites-available/rpc.markettrackerx.com
sudo sed -i '/http2 on;/d' /etc/nginx/sites-available/rpc.markettrackerx.com
```

### "cannot load certificate ... No such file or directory"
This happens because the config references `/etc/letsencrypt/live/.../fullchain.pem` before Certbot has actually issued a cert — `nginx -t` fails and blocks the reload Certbot's `--nginx` plugin needs.

**Fix — issue the cert first, then enable HTTPS:**

1. Comment out the entire HTTPS `server { listen 443 ssl http2; ... }` block (leave the port-80 block, including the `/.well-known/acme-challenge/` location, active).
2. `sudo mkdir -p /var/www/certbot`
3. Test and reload with HTTP only:
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```
4. Issue the cert via webroot:
   ```bash
   sudo certbot certonly --webroot -w /var/www/certbot -d rpc.markettrackerx.com
   ```
5. Uncomment the HTTPS block, then:
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

Alternative one-liner that sometimes works around this automatically: `sudo certbot --nginx -d rpc.markettrackerx.com` (try this first — fall back to the webroot method above if it errors on the missing cert).

---

## 7. Testing after certificate issuance

Once `nginx -t` passes and reload succeeds, verify end-to-end:

**a) Confirm the cert is live and matches the domain:**
```bash
echo | openssl s_client -connect rpc.markettrackerx.com:443 -servername rpc.markettrackerx.com 2>/dev/null | openssl x509 -noout -dates -subject
```
Should show `subject=CN = rpc.markettrackerx.com` and a valid (non-expired) date range.

**b) Confirm HTTPS is reachable and headers look right:**
```bash
curl -I https://rpc.markettrackerx.com
```
Expect a `200`/`405`/whatever your RPC backend returns for a bare GET — the key thing is it responds over HTTPS without a cert error.

**c) Confirm HTTP → HTTPS redirect works:**
```bash
curl -I http://rpc.markettrackerx.com
```
Expect a `301` pointing to the `https://` URL.

**d) Send an actual JSON-RPC request end-to-end:**
```bash
curl -X POST https://rpc.markettrackerx.com \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```
Expect a JSON response like:
```json
{"jsonrpc":"2.0","id":1,"result":"0x..."}
```
If you get this, the proxy is correctly forwarding to your local RPC backend over HTTPS.

**e) (If WebSocket is enabled) test WS upgrade:**
```bash
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: $(openssl rand -base64 16)" \
  https://rpc.markettrackerx.com
```
Expect a `101 Switching Protocols` response.

**f) Confirm auto-renewal is scheduled:**
```bash
sudo systemctl status certbot.timer
sudo certbot renew --dry-run
```

**g) Confirm the RPC port isn't publicly reachable directly (hardening check):**
```bash
curl -m 5 http://45.249.8.94:8545
```
This should time out / refuse from outside — if it responds, your backend is bound to `0.0.0.0` and reachable without going through Nginx, which bypasses your rate limiting and TLS. Bind it to `127.0.0.1` or firewall the port off.

---

## 8. Recommended hardening (optional but worth doing for a public RPC endpoint)

- **Restrict exposed methods**: publicly exposing an unrestricted JSON-RPC node can allow admin/debug methods (`admin_*`, `debug_*`, `personal_*`) to leak. If your node doesn't already disable these at the client level, consider filtering at Nginx with a `map`/`if` on the request body, or better, disable them in the node's own config.
- **Rate limit** aggressively (the `limit_req` block above) — RPC endpoints are common targets for scraping/abuse.
- **Firewall**: only allow Nginx (443/80) inbound publicly; block direct external access to port `8545` (e.g. `ufw deny 8545` or bind the RPC service to `127.0.0.1` only, not `0.0.0.0`).
- **Monitoring**: watch `access.log` for spammy IPs and consider `fail2ban` for repeated abuse patterns.

---

## Quick checklist

- [ ] DNS `A` record confirmed resolving to `45.249.8.94`
- [ ] RPC backend confirmed listening locally
- [ ] Nginx server block created and enabled
- [ ] `nginx -t` passes
- [ ] Certbot issued and auto-renew verified (`certbot renew --dry-run`)
- [ ] `openssl s_client` confirms valid cert for the domain
- [ ] `curl -I http://...` confirms 301 redirect to HTTPS
- [ ] `curl` JSON-RPC test against `https://rpc.markettrackerx.com` returns valid response
- [ ] Port `8545` blocked from direct public access (verified with external `curl`)