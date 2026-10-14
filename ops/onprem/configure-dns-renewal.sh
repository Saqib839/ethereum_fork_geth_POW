#!/bin/sh
set -eu
if [ "$(id -u)" -ne 0 ]; then
    echo 'Run with sudo after configuring /root/.aws/credentials.' >&2
    exit 1
fi
# Reconfigure performs staging validation and saves the new authenticator only
# after it succeeds. Keep the existing production certificate in place.
certbot reconfigure --non-interactive --cert-name rpc.markettrackerx.com --dns-route53 --run-deploy-hooks
certbot renew --non-interactive --cert-name rpc.markettrackerx.com --dry-run --run-deploy-hooks
systemctl enable --now certbot.timer
