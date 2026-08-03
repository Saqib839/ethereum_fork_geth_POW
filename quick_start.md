# Quick Start Guide

Fast-start guide for launching a private Ethereum PoW chain in production with Geth v1.10.26-stable.

Setup:
- one RPC-only node
- one separate mining node

This keeps roles simple and avoids mixing wallet unlocks/mining into the RPC node.

---

## 1. Prerequisites

- Geth v1.10.26-stable installed and available in your PATH
- a Linux or macOS server
- a repository copy with [genesis.json](genesis.json) and [password.txt](password.txt)

Verify the version:

```bash
geth version
```

Expected output should begin with:

```text
1.10.26
```

---

## 2. Create the working directories

```bash
mkdir -p ./rpc_node1 ./miner_node1 ./logs
```

---

## 3. Create the miner account

```bash
geth account new --datadir ./miner_node1
```

Save the generated address — you'll use it in the systemd service below.

Create the password file if it doesn't already exist:

```bash
printf 'your-password-here\n' > password.txt
chmod 600 password.txt
```

> **Important:** the password in this file must exactly match the one you entered interactively when running `geth account new` above — it's what `--unlock`/`--password` will use to decrypt the keystore in the miner service.

---

## 4. Initialize the chain

If starting over from scratch, wipe old data first:
```bash
rm -rf ./rpc_node1/geth ./rpc_node1/keystore ./miner_node1/geth ./miner_node1/keystore
```

```bash
geth init --datadir ./rpc_node1 genesis.json
geth init --datadir ./miner_node1 genesis.json
```

---

## 5. Get both nodes' enodes

Each node needs the *other's* enode as a bootnode, so they can rediscover each other even if one restarts.

An enode is generated from a node's own node key (`<datadir>/geth/nodekey`), created the first time that node starts up — this does **not** require the other node to be running. So do this one node at a time, in any order:

```bash
# 1. Start the miner alone, briefly
geth --datadir ./miner_node1 --networkid 5356 --port 30304 console
```

Inside the console:

```js
admin.nodeInfo.enode
```

It will print something like:

```text
enode://a1b2c3...@[::]:30304
```

Copy the `<pubkey>` portion (between `enode://` and `@`), then exit with `exit`.

```bash
# 2. Now start the RPC node alone, briefly
geth --datadir ./rpc_node1 --networkid 5356 --port 30303 console
```

Run `admin.nodeInfo.enode` again, copy its pubkey, and `exit`.

You now have both enodes: the miner's goes into `--bootnodes` on the **RPC** service, and the RPC node's goes into `--bootnodes` on the **miner** service (below). The node key persists in each datadir, so these enodes stay valid once you start the real systemd services.

> **Note:** If a node's datadir/node key is ever deleted or regenerated, its enode changes and you must update the bootnode value on the *other* node. Use `127.0.0.1` if both nodes are on the same server, or the real IP if on separate machines.

---

## 6. Production systemd services

### 6.1 Create the logs directory

```bash
mkdir -p ./logs
```

### 6.2 Create the mining service
Create a file named:

```bash
sudo nano /etc/systemd/system/geth-miner.service
```

Paste the following content for the Miner node:

```ini
[Unit]
Description=Geth PoW mining node
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/your-user/ethereum_fork_geth_POW
User=your-user
Group=your-user
ExecStart=/usr/local/bin/geth --datadir /home/your-user/ethereum_fork_geth_POW/miner_node1 \
  --networkid 5356 \
  --http --http.addr 0.0.0.0 --http.port 8546 \
  --http.api eth,net,web3,personal,miner,admin \
  --port 30304 \
  --http.corsdomain "*" \
  --http.vhosts "*" \
  --bootnodes "enode://<rpc-enode>@127.0.0.1:30303" \
  --unlock 0xYOUR_ADDRESS \
  --password /home/your-user/ethereum_fork_geth_POW/password.txt \
  --miner.etherbase 0xYOUR_ADDRESS \
  --mine \
  --allow-insecure-unlock
Restart=always
RestartSec=10
StandardOutput=append:/home/your-user/ethereum_fork_geth_POW/logs/geth-miner.log
StandardError=append:/home/your-user/ethereum_fork_geth_POW/logs/geth-miner.log

[Install]
WantedBy=multi-user.target
```

### 6.3 Create the RPC service
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
ExecStart=/usr/local/bin/geth --datadir /home/your-user/ethereum_fork_geth_POW/rpc_node1 \
  --networkid 5356 \
  --http --http.addr 0.0.0.0 --http.port 8545 \
  --http.api eth,net,web3 \
  --port 30303 \
  --http.corsdomain "*" \
  --http.vhosts "*" \
  --bootnodes "enode://<miner-enode>@127.0.0.1:30304"
Restart=always
RestartSec=10
StandardOutput=append:/home/your-user/ethereum_fork_geth_POW/logs/geth-rpc.log
StandardError=append:/home/your-user/ethereum_fork_geth_POW/logs/geth-rpc.log

[Install]
WantedBy=multi-user.target
```

Replace `your-user`, the repository path, `0xYOUR_ADDRESS`, `<miner-enode>`, and `<rpc-enode>` with your actual values.

### 6.4 Enable and start the services

```bash
sudo systemctl daemon-reload
sudo systemctl enable geth-miner.service
sudo systemctl enable geth-rpc.service
sudo systemctl start geth-miner.service
sudo systemctl start geth-rpc.service
```

### 6.5 Check status

```bash
sudo systemctl status geth-miner.service
sudo systemctl status geth-rpc.service
```

---

## 7. Exposing the RPC node publicly (for MetaMask/wallets)

The RPC node (not the miner) is the one you point wallets at. To expose it safely:

- **Put a reverse proxy (nginx, Caddy, etc.) in front of it** on 443 with a TLS cert, forwarding to `127.0.0.1:8545`. Don't put port 8545 directly on the internet — bind geth's `--http.addr` to `127.0.0.1` instead of `0.0.0.0` once the proxy is in place, so only the proxy can reach it.
- **`--http.api` should stay `eth,net,web3`** on this public node (already set above) — that's everything MetaMask needs. You still have full `admin`/`personal` access locally via `geth attach ./rpc_node1/geth.ipc`, since IPC isn't restricted by `--http.api`.
- **`--http.corsdomain "*"`** is needed so browser wallets can call in from any dApp origin — keep it, or narrow it to specific domains if you control which sites will connect.
- **`--http.vhosts`** should include whatever hostname the proxy forwards with (or keep `"*"` if you're not picky about the `Host` header).
- **Consider rate-limiting at the proxy** — a public RPC endpoint is an open door to spam/DoS once the address is known.
- **MetaMask setup**: Settings → Networks → Add network → RPC URL = your proxy's HTTPS URL, Chain ID = your `networkid` (5356), currency symbol = whatever you defined in `genesis.json`.

---

## 8. Useful commands

Attach to the miner:

```bash
geth attach ./miner_node1/geth.ipc
```

Attach to the RPC node:

```bash
geth attach ./rpc_node1/geth.ipc
```

Check the chain:

```js
eth.blockNumber
eth.chainId()
eth.getBlock("latest")
```

Mining controls:

```js
miner.start()
miner.stop()
```

---

## 8. Notes

- Keep the same datadir and node key files if you want stable discovery after restart.
- If you delete the datadir or node key files, the enode changes and you must update the bootnode value again.
- The RPC node is intentionally separate from the mining node for a cleaner deployment.
- The miner service exposes `personal`, `miner`, and `admin` over RPC on `0.0.0.0` with an unlocked account — restrict this to a firewall/VPN in production, since it's a much more sensitive attack surface than the RPC node.