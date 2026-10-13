# HTTPS RPC

For wallet access, place Nginx on **443** in front of local `127.0.0.1:8545`. Open TCP 80 only if needed for certificate validation. Keep Geth RPC/Engine ports private.

Use your domain and TLS certificate with this location block:

```nginx
location / {
    proxy_pass http://127.0.0.1:8545;
    proxy_set_header Host localhost;
    proxy_connect_timeout 2s;
    proxy_read_timeout 30s;
}
```

```bash
sudo nginx -t
sudo systemctl reload nginx
```

For two RPC backends, use [rpc-failover.nginx.conf.example](ops/onprem/rpc-failover.nginx.conf.example). Replace its domain, certificate paths, and AWS VPN address. AWS RPC must listen on a private interface reachable by the proxy, with 8545 restricted to that proxy. Both backends must be synchronized to the same chain.

Clients must retry failed POSTs. Use redundant proxies or client endpoint failover for a whole-site outage. Add CORS headers if required by your browser dApp.

The existing `ops/rpc-https-bootstrap*` files are from the AWS deployment; review their host-specific settings before reusing them locally.
