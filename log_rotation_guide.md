## Automate log rotation with logrotate

This guide explains how to rotate every log file inside a dedicated `logs` folder so your node keeps running without filling the disk.

### Step 1: Create a logs folder

If you do not already have one, create a folder for your logs:

```bash
mkdir -p ./logs
```

Put your log files in this folder, for example:

```bash
mkdir -p ./logs
cp geth.log ./logs/
```

### Step 2: Install logrotate

If you want automatic rotation, install `logrotate` if it is not already present:

```bash
sudo apt update
sudo apt install -y logrotate
```

### Step 3: Create a logrotate config for the whole logs folder

Create a config file such as `/etc/logrotate.d/geth`:

```bash
sudo tee /etc/logrotate.d/geth >/dev/null <<'EOF'
/your/path/to/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    copytruncate
}
EOF
```

Replace `/your/path/to` with the actual directory where your repository is stored.

For example, if your project is at `/home/your-user/ethereum_fork_geth_POW`, then the config should look like:

```bash
sudo tee /etc/logrotate.d/geth >/dev/null <<'EOF'
/home/your-user/ethereum_fork_geth_POW/logs/*.log {
    su ovextech ovextech
    daily
    rotate 7
    compress
    missingok
    notifempty
    copytruncate
}
EOF
```

```bash 
sudo chown ovextech:ovextech /home/ovextech/ethereum-pow-blockchain/logs/*.log
```

### Step 4: Test it manually

Run:

```bash
sudo logrotate -f /etc/logrotate.d/geth
```

### Step 5: Verify rotation

Check the folder contents:

```bash
ls -lh ./logs
```

You should see rotated files such as `geth.log.1` or compressed versions depending on the settings.

---

## Notes

- `copytruncate` is useful because it preserves the existing log file path while rotating it.
- This rule matches all `.log` files inside the `logs` folder.
- If you are using `systemd`, the preferred approach is often to let `journalctl` handle logs rather than a plain text file.
