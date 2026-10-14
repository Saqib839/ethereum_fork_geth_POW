Secondary RPC: rpc.markettrackerx.com
==================================

Confirmed ingress is **45.249.8.94**. External HTTP and HTTPS requests with
unique paths appeared in this VM's Nginx access log on 2026-10-14. The VM's
private interface is 192.168.114.24; the outbound IP is 149.40.242.241.
Public-IP requests from this VM time out (a likely NAT hairpin limitation).

Nginx forwards RPC to 127.0.0.1:8545 with `Host: localhost`. Geth still accepts
only localhost and 127.0.0.1 and remains bound to loopback. The readiness
listener is also loopback-only, on 18545.

Both local nodes and AWS report chain ID 5356 / 0x14ec and genesis:

```
0xdd1301fd0ca034e5f60c87919d01933dcc563333f6064f24d6a256b5f03f9bc8
```

Local and AWS canonical hashes were compared at the same block height and
matched. Both local nodes have direct connections to both configured AWS
nodes. No datadir was deleted or initialized.

`ethereum-rpc-health.service` is enabled at boot. Nginx `/healthz` on both
HTTP and HTTPS checks the local RPC, chain ID, genesis, syncing status,
timestamp (at most 300 seconds old, at most 30 seconds in the future), and
balance/code state reads pinned to the canonical latest block hash.
Success is exactly `200 rpc-ready`; failure is `503 rpc-not-ready`.
Nginx also maps an unavailable health listener to 503. Health checks do not
depend on AWS remaining available.

Local verification with the actual TLS hostname:

```bash
curl --noproxy '*' --resolve rpc.markettrackerx.com:443:127.0.0.1 \
  https://rpc.markettrackerx.com/healthz
curl --noproxy '*' --resolve rpc.markettrackerx.com:443:127.0.0.1 \
  https://rpc.markettrackerx.com -H 'Content-Type: application/json' \
  --data '{"jsonrpc":"2.0","id":1,"method":"eth_chainId","params":[]}'
```

From another machine, substitute **45.249.8.94** for 127.0.0.1. Do not add
`-k`: the Let's Encrypt certificate should pass trust and hostname checks.
The current certificate expires 2026-12-12 04:36:01 UTC.

Remaining certificate renewal setup
----------------------------------

The Route 53 Certbot plugin is installed, the renewal timer is enabled, and
an Nginx reload deploy hook is installed. DNS-01 reconfiguration was attempted
but failed with `Unable to locate credentials`. The saved renewal method
therefore remains HTTP-01; renewal while DNS points to AWS is **not yet proven**.

In the AWS account that owns markettrackerx.com's public hosted zone:

1. Create a dedicated IAM user, for example `rpc-secondary-cert-renewal`.
2. Give it an inline policy using `route53-certbot-policy.json` in this directory.
   The policy permits changing only the exact ACME TXT record and cannot
   change the RPC A records. You may restrict its hostedzone ARN to your zone ID.
3. Create an access key for that user. Save the ID and secret securely.
4. In your SSH terminal, run the following and paste the keys at the hidden
   prompts. Never send them in chat:

```bash
sudo python3 /home/ovextech/ethereum-pow-blockchain/ops/onprem/set-renewal-credentials.py
```

Then configure and verify unattended renewal:

```bash
sudo sh /home/ovextech/ethereum-pow-blockchain/ops/onprem/configure-dns-renewal.sh
```

This performs staging validation, saves DNS-01 only on success, and tests the
saved renewal settings. It preserves the existing production certificate.

Route 53 settings
-----------------

Authoritative DNS currently returns 149.40.242.241 and 16.60.82.161. This VM's
secondary A record must use **45.249.8.94**. No DNS records were changed here.

Use `route53-secondary-healthcheck.json` for a health check addressed directly
to 45.249.8.94, with Host/SNI rpc.markettrackerx.com, HTTPS port 443, path
/healthz, and string match rpc-ready. Associate it with the secondary failover
A record. Specify the primary's IP explicitly in its separate health check.
Do not have either check discover its target from the shared failover hostname.

Official references:

- https://certbot-dns-route53.readthedocs.io/en/stable/
- https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/specifying-conditions-route53.html
- https://docs.aws.amazon.com/Route53/latest/APIReference/API_HealthCheckConfig.html
