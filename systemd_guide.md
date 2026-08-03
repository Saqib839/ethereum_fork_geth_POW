# systemd Guide for Auto-Starting Geth on Server Reboot

This guide shows how to run your Geth PoW node as a `systemd` service so it starts automatically after a server reboot or crash. This is the recommended approach instead of `nohup`.


## Step 2: Initialize the chain

Run this once for a fresh chain:

```bash
geth init --datadir ./node1 genesis.json
```

If you are launching a new chain from scratch, make sure the old data directory is removed first if needed:

```bash
rm -rf ./node1/geth ./node1/keystore
geth init --datadir ./node1 genesis.json
```

---

## Step 3: Create the systemd service file

Create a file named:

```bash
sudo nano /etc/systemd/system/geth-rpc.service
```

Paste the following content for the RPC-only node:

```ini
[Unit]
Description=Geth PoW RPC node
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/your-user/ethereum_fork_geth_POW
User=your-user
Group=your-user
ExecStart=/usr/local/bin/geth --datadir /home/your-user/ethereum_fork_geth_POW/node1 \
  --networkid 5356 \
  --rpc --rpcaddr 0.0.0.0 --rpcport 8546 \
  --rpcapi eth,net,web3,personal,admin \
  --port 30303
Restart=always
RestartSec=10
StandardOutput=append:/home/your-user/ethereum_fork_geth_POW/logs/geth-rpc.log
StandardError=append:/home/your-user/ethereum_fork_geth_POW/logs/geth-rpc.log

[Install]
WantedBy=multi-user.target
```

Replace:

- `your-user` with your Linux username
- `/home/your-user/ethereum_fork_geth_POW` with the full path to this repository

This runs a pure RPC node with no password and no mining.

If you want a separate mining node, create a second service file such as `/etc/systemd/system/geth-miner.service` with this launch command:

```ini
[Unit]
Description=Geth PoW mining node
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/your-user/ethereum_fork_geth_POW
User=your-user
Group=your-user
ExecStart=/usr/local/bin/geth --datadir /home/your-user/ethereum_fork_geth_POW/node2 \
  --networkid 5356 \
  --rpc --rpcaddr 0.0.0.0 --rpcport 8545 \
  --rpcapi eth,net,web3,personal,miner,admin \
  --port 30304 \
  --unlock 0x80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2 \
  --password /home/your-user/ethereum_fork_geth_POW/password.txt \
  --miner.etherbase 0x80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2 \
  --mine \
  --allow-insecure-unlock
Restart=always
RestartSec=10
StandardOutput=append:/home/your-user/ethereum_fork_geth_POW/logs/geth-miner.log
StandardError=append:/home/your-user/ethereum_fork_geth_POW/logs/geth-miner.log

[Install]
WantedBy=multi-user.target
```

Make sure the logs directory exists:

```bash
mkdir -p /home/your-user/ethereum_fork_geth_POW/logs
```

---

## Step 4: Reload systemd

Run:

```bash
sudo systemctl daemon-reload
```

---

## Step 5: Enable the service

Enable it so it starts automatically on boot:

```bash
sudo systemctl enable geth-rpc.service
```

---

## Step 6: Start the service

```bash
sudo systemctl start geth-rpc.service
```

---

## Step 7: Check the service status

```bash
sudo systemctl status geth-rpc.service
```

You should see that the service is active and running.

---

## Step 8: Check logs

```bash
sudo journalctl -u geth-rpc.service -f
```

Or if you are logging to the file directly:

```bash
tail -f /home/your-user/ethereum_fork_geth_POW/logs/geth.log
```

---

## Step 9: Restart or stop the service

Restart:

```bash
sudo systemctl restart geth-rpc.service
```

Stop:

```bash
sudo systemctl stop geth-rpc.service
```

---

## Important notes

- This setup is intended for a private or trusted environment.
- `--allow-insecure-unlock` is only safe on a private network.
- If your account is not in the keystore for the datadir, the service will fail to unlock it.
- Make sure the password file exists and is readable by the system user.
- For a brand-new chain launch, initialize the genesis first and only then start the service.

---

## Why this is better than nohup

Using systemd gives you:

- automatic startup after reboot
- automatic restart after crashes
- cleaner process management
- better logging through `journalctl`
- easier maintenance and monitoring
