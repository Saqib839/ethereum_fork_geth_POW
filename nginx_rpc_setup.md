# Nginx RPC proxy for `rpc.markettrackerx.com`

## Automatic setup installed on 2026-10-13

The VM now has `rpc-https-bootstrap.timer` enabled. Every five minutes,
`/usr/local/sbin/rpc-https-bootstrap` checks the authoritative DNS server and
Cloudflare/Google resolvers. Once the A record is exactly `16.60.82.161` and no
AAAA record exists, it requests a Let's Encrypt certificate using the existing
ACME webroot, installs `/etc/nginx/rpc-https-ready.conf` as the active RPC site,
validates Nginx, and reloads it. Failed certificate requests retry at most hourly.
The previous site is restored if Nginx validation or reload fails.

The HTTPS proxy forwards to `127.0.0.1:8545` and HTTP redirects to HTTPS.
`certbot.timer` handles renewals, with a deploy hook that validates and reloads
Nginx. Source files for the installed configuration and automation are in `ops/`.
Update the script's `expected_ip` if the VM's public IP changes.

Check progress with:

```bash
sudo journalctl -u rpc-https-bootstrap.service -n 20 --no-pager
systemctl list-timers rpc-https-bootstrap.timer certbot.timer
```

At installation, DNS still returned `45.249.8.94`, so certificate issuance and
end-to-end HTTPS on this VM remain pending. Port 80 must be publicly reachable
for issuance, and port 443 for HTTPS. The chain mismatch described below still
exists: cutover will serve the local node's different genesis.

The following sections describe the earlier state and manual setup alternative;
the installed automation now performs certificate issuance and proxy activation.

This guide prepares Nginx now and finishes the HTTPS proxy after the subdomain points to this server. Geth's HTTP RPC listens only on `127.0.0.1:8545`; Nginx is the only intended public entry point.

## Current server state

- Nginx is installed, enabled, and running.
- Nginx's default HTTP server rejects requests for unknown hostnames, and its default TLS server rejects TLS handshakes for unknown SNI names.
- The `rpc.markettrackerx.com` HTTP server serves only ACME challenge files and returns `503` for other requests until HTTPS is ready.
- No certificate or domain-specific HTTPS server exists yet, so there is no public RPC proxy at this stage.
- At the last check, EC2 instance metadata reported this instance's assigned public IPv4 as `16.60.82.161`, while `rpc.markettrackerx.com` still resolved to `45.249.8.94`. The DNS record is not yet pointed at this instance.
- The existing DNS target is live: HTTP redirects to HTTPS, the TLS certificate is valid, and JSON-RPC responds there. A cutover will replace that working endpoint.

Nginx's active site files are `/etc/nginx/sites-available/geth-rpc` and `/etc/nginx/sites-available/rpc.markettrackerx.com`. The latter is already enabled.

## Before cutover: confirm the chain

As checked on 2026-10-09, both RPC endpoints report chain ID `0x14ec` (5356), but their genesis block hashes differ:

- Current public endpoint: `0x2ed59437dd2d78b1644f4455c2224eace1698c8ffbc54afd8668abfc41d64098`
- New instance: `0xdd1301fd0ca034e5f60c87919d01933dcc563333f6064f24d6a256b5f03f9bc8`

They are separate chains. Repository history confirms the current public endpoint matches `bef06ac:genesis.json`; the new instance uses the current `genesis.json`. The active datadirs were initialized with the new genesis, so changing the JSON file alone will not convert them. Preserving the existing chain would require a safe migration into a datadir initialized from the historical genesis and working peer connectivity. TCP connections from this instance to the current endpoint's P2P ports `30303` and `30304` timed out during the check.

Before changing DNS, decide whether the subdomain should keep serving the existing chain or move to the new chain. If keeping the existing chain, do not cut over until the new node has the matching genesis and has caught up.

Recheck each endpoint's genesis block with:

```bash
curl -sS https://rpc.markettrackerx.com \
  -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["0x0",false],"id":1}'

curl -sS http://127.0.0.1:8545 \
  -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["0x0",false],"id":1}'
```

## 1. Point the subdomain when ready

In Route 53, update the `A` record for `rpc.markettrackerx.com` to the public IPv4 or Elastic IP assigned to this EC2 instance. Do not use its private `10.x.x.x` address. Allow inbound TCP ports 80 and 443 in the instance's security group.

Wait until this resolves to the instance's public address:

```bash
dig +short rpc.markettrackerx.com
```

The ACME challenge path is already configured at `/var/www/certbot`. Until DNS points here, certificate issuance will fail because Let's Encrypt will reach the old DNS target.

## 2. Issue the certificate

Certbot is installed. Once DNS resolves to this server and inbound port 80 is reachable, issue the certificate with the webroot method:

```bash
sudo certbot certonly --webroot \
  -w /var/www/certbot \
  -d rpc.markettrackerx.com
```

## 3. Enable HTTPS and the RPC proxy

The default deny rules in `/etc/nginx/sites-available/geth-rpc` are already active. After Certbot has created both certificate files, replace `/etc/nginx/sites-available/rpc.markettrackerx.com` with:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name rpc.markettrackerx.com;

    location ^~ /.well-known/acme-challenge/ {
        root /var/www/certbot;
        default_type text/plain;
        try_files $uri =404;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name rpc.markettrackerx.com;

    ssl_certificate /etc/letsencrypt/live/rpc.markettrackerx.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/rpc.markettrackerx.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    client_max_body_size 2m;

    location / {
        proxy_pass http://127.0.0.1:8545;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 10s;
        proxy_read_timeout 300s;
        proxy_send_timeout 60s;
    }
}
```

Then validate and reload Nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

The default TLS server rejects connections without the expected SNI hostname. The RPC proxy is only in the HTTPS server block for `rpc.markettrackerx.com`.

## 4. Verify the endpoint

Send a JSON-RPC request through HTTPS:

```bash
curl -sS https://rpc.markettrackerx.com \
  -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'
```

The expected chain ID is `0x14ec` (5356). Confirm certificate renewal is scheduled:

```bash
sudo systemctl status certbot.timer
sudo certbot renew --dry-run
```

Geth should continue binding RPC to `127.0.0.1:8545`; do not expose port 8545 directly in the EC2 security group. The miner's authenticated Engine API on port 8551 and RPC node's Engine API on 8552 should also remain private.
