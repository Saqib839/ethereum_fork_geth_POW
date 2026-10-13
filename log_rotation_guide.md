# Log rotation

The node installer creates `logs/geth-rpc.log` and `logs/geth-miner.log`, then installs `/etc/logrotate.d/ethereum-pow-onprem` and enables `ethereum-pow-logrotate.timer`.

Rotation runs **daily**, retains **seven compressed archives**, and uses `copytruncate` so the services continue writing without restarting. A few lines can be lost during copying/truncation.

```bash
# Check automatic rotation
systemctl list-timers ethereum-pow-logrotate.timer

# Rotate immediately
sudo logrotate -f /etc/logrotate.d/ethereum-pow-onprem
ls -lh logs/
```

For manual installation, replace the path and Linux user/group below:

```text
"/home/ovextech/ethereum-pow-blockchain/logs/*.log" {
    su ovextech ovextech
    daily
    rotate 7
    compress
    missingok
    notifempty
    copytruncate
}
```

The installer enables scheduling automatically; use it for this setup.
