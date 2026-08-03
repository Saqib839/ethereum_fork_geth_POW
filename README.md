# Standalone Ethereum PoW Chain (Geth v1.10.26-stable)

This repository is a private Ethereum network configuration for running a Proof-of-Work (PoW) chain with Geth 1.10.26-stable, using Ethash (not Clique). This document covers everything you need to understand and prepare **before** you actually launch a node — installing Geth, setting up accounts and genesis, and what every relevant flag does. For the exact commands to bring the chain up in production (systemd services, roles split across two nodes, etc.), see the quick-start guide.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Install Geth](#2-install-geth)
3. [Create a Miner Account](#3-create-a-miner-account)
4. [Prepare the Password File](#4-prepare-the-password-file)
5. [Initialize the Genesis](#5-initialize-the-genesis)
6. [Node Roles: RPC vs. Miner](#6-node-roles-rpc-vs-miner)
7. [Getting a Node's Enode](#7-getting-a-nodes-enode)
8. [Flag Reference](#8-flag-reference)
9. [Useful Console Commands](#9-useful-console-commands)
10. [Import an Existing Wallet Key](#10-import-an-existing-wallet-key)
11. [Troubleshooting](#11-troubleshooting)
12. [Notes](#12-notes)

---

## 1. Prerequisites

- A Linux or macOS machine
- `git`, `make`, and a compiler toolchain (only needed if building from source)
- Basic terminal experience
- Internet access if downloading or building Geth

---

## 2. Install Geth

### Option A: Download a prebuilt binary

Download the Geth 1.10.26 binary for your platform from the official Geth releases page and place it in a directory on your `PATH`, such as `/usr/local/bin`.

### Option B: Build from source

```bash
sudo apt update
sudo apt install -y golang-go git build-essential

git clone https://github.com/ethereum/go-ethereum.git
cd go-ethereum
git checkout v1.10.26
make geth
sudo cp build/bin/geth /usr/local/bin/geth
```

### Verify the installation

```bash
geth version
```

You should see output beginning with `1.10.26`. If `geth` isn't found, run `which geth` and confirm the binary's directory is on your `PATH`.

---

## 3. Create a Miner Account

This account receives mining rewards and acts as the coinbase address:

```bash
geth account new --datadir ./node1
```

You'll be prompted for a password — choose a strong one and remember it. The output includes a public address like:

```text
Public address of the key: 0x1234567890abcdef1234567890abcdef12345678
```

Save this address; you'll reference it wherever `--unlock` or `--miner.etherbase` is used.

---

## 4. Prepare the Password File

For non-interactive startup (needed so the account can unlock automatically when a service restarts):

```bash
echo "your-password-here" > password.txt
chmod 600 password.txt
```

This must be the same password you set in step 3. Keep this file private — it decrypts your keystore.

---

## 5. Initialize the Genesis

```bash
geth init --datadir ./node1 genesis.json
```

Expected result: `Successfully wrote genesis state`.

If it fails, check that the file path is correct, the genesis file is valid JSON, and your Geth version is compatible.

**If you change `genesis.json` after initializing**, wipe the old state first — old chain data and a new genesis config conflict:

```bash
rm -rf ./node1/geth ./node1/keystore
geth init --datadir ./node1 genesis.json
```

---

## 6. Node Roles: RPC vs. Miner

This setup runs two Geth processes with different jobs, each with its own `--datadir`:

- **RPC node** — serves `eth`/`net`/`web3` JSON-RPC calls for wallets and dApps (e.g. MetaMask). Doesn't mine, doesn't hold an unlocked account, and is the only node meant to ever be reachable from outside your own machine/network.
- **Miner node** — holds the unlocked coinbase account and produces blocks. Has no reason to expose any RPC API to anything but you, locally — see the [flag reference](#8-flag-reference) below for why.

Splitting these two roles keeps a mistake on one node (say, a misconfigured CORS setting on the public RPC node) from ever touching the account that can sign transactions.

---

## 7. Getting a Node's Enode

Each node needs the *other's* enode as a bootnode so they can find each other on the network — including after a restart.

An enode is derived from a node's own node key (`<datadir>/geth/nodekey`), generated the first time that node starts. You don't need both nodes running at once to get this — do it one at a time:

```bash
geth --datadir ./node1 --networkid 5356 --port 30303 console
```

Inside the console:

```js
admin.nodeInfo.enode
```

This prints something like `enode://a1b2c3...@[::]:30303` — copy the part between `enode://` and `@`, then `exit`. Repeat for the other node on its own port.

The miner's pubkey goes into the RPC node's `--bootnodes`, and vice versa. If a datadir or node key is ever deleted, the enode changes and you'll need to update it on the other node.

---

## 8. Flag Reference

Every flag you'll actually use across both nodes, grouped by what it controls. `--networkid` must always match the `chainId` in `genesis.json`, or peers won't recognize each other.

### Node identity & networking

| Flag | What it does | Why it matters |
|---|---|---|
| `--datadir <path>` | Where chain data and the keystore live | Each node needs its own — sharing one between the RPC and miner node would mix their state and keys |
| `--networkid <n>` | Declares which private network this node belongs to | Must match `chainId` in `genesis.json`; prevents accidentally connecting to mainnet or a public testnet |
| `--port <n>` | P2P listening port for peer connections | Needs to be reachable by the other node (directly, or via firewall rule) for peer discovery to work |
| `--bootnodes <enode>` | Enode URL(s) to contact on startup for peer discovery | Without at least one, an isolated node may never find its peer |
| `console` | Opens an interactive JavaScript console attached to the running node | Lets you run `admin.*`, `eth.*`, `miner.*` commands directly |

### HTTP-RPC (only relevant to the RPC node)

| Flag | What it does | Why it matters |
|---|---|---|
| `--http` | Enables the JSON-RPC-over-HTTP server | Required for anything (MetaMask, scripts) to talk to the node over the network |
| `--http.addr <ip>` | Interface the HTTP server binds to | `127.0.0.1` = reachable only from the same machine (safe default, use with a reverse proxy); `0.0.0.0` = reachable from any network interface — never set this without a firewall/proxy already in place |
| `--http.port <n>` | Port for the HTTP-RPC server | Default `8545`; only needs to be memorable, not secret |
| `--http.api <list>` | Which API namespaces are exposed over HTTP | `eth,net,web3` is everything a wallet needs and is safe to expose publicly. `personal`, `miner`, `admin` grant account/mining/node-control access — never include these in an HTTP API list that's reachable off-host |
| `--http.corsdomain <list>` | Which browser origins may call in | Browsers enforce CORS, so this is what lets a dApp's JavaScript actually reach your endpoint; `"*"` allows any site, narrow it if you know which dApps will connect |
| `--http.vhosts <list>` | Which `Host` header values the server accepts | Guards against DNS-rebinding attacks; should match whatever hostname your reverse proxy forwards with |

### Account & mining (only relevant to the miner node)

| Flag | What it does | Why it matters |
|---|---|---|
| `--unlock <address>` | Unlocks the given account at node startup | This is a startup-time operation, separate from any RPC call — it works whether or not HTTP/RPC is enabled at all |
| `--password <path>` | Password file used to decrypt the keystore for `--unlock` | Lets startup be non-interactive (needed for a systemd service that can restart unattended) |
| `--miner.etherbase <address>` | Sets which account receives block rewards | Must be an account that exists in this node's own keystore |
| `--mine` | Starts mining immediately on launch | Without it, the node syncs and validates but never produces blocks |
| `--allow-insecure-unlock` | Removes Geth's default block on unlocking accounts via the `personal_unlockAccount` **RPC call** when HTTP/WS is enabled | This flag only matters if the node also has `--http`/`--ws` enabled — Geth added the block because an unlocked account behind a network-reachable RPC endpoint is directly drainable. **This setup's miner node has no need for this flag at all**: keep `--http` off the miner entirely and control it locally via IPC, and the restriction this flag removes never comes into play |

### IPC (local control — enabled by default on both nodes)

| Flag | What it does | Why it matters |
|---|---|---|
| `--ipcpath <path>` | Filename for the IPC socket within the datadir | Rarely needs changing; defaults to `geth.ipc` inside `--datadir` |
| `--ipcdisable` | Turns off the IPC socket | Don't use this — IPC is your safe, local-only way to run `personal`/`miner`/`admin` commands without ever opening a network port for them |

---

## 9. Useful Console Commands

Attach with `geth attach ./node1/geth.ipc` (or `./node2/geth.ipc` for the miner), then:

**Chain checks**
```js
eth.blockNumber
eth.chainId()
eth.getBlock("latest")
```

**Account checks**
```js
eth.accounts
eth.getBalance(eth.accounts[0])
web3.fromWei(eth.getBalance(eth.accounts[0]), "ether")
```

**Mining controls** (on the miner node)
```js
miner.start()
miner.stop()
```

**Networking**
```js
admin.nodeInfo.enode
admin.peers
net.peerCount
```

---

## 10. Import an Existing Wallet Key

If you already have a private key you want to use instead of generating a new one:

```bash
echo -n "your_raw_private_key_here" > private_key.txt
echo "your-password-here" > password.txt
chmod 600 password.txt
geth account import --datadir ./node1 --password ./password.txt private_key.txt
rm private_key.txt
```

Verify with `geth account list --datadir ./node1`.

---

## 11. Troubleshooting

- **`Fatal: Error starting protocol stack: authentication needed`** — check the password file exists and its path matches what's passed to `--password`.
- **No peers, or no blocks being produced** — confirm the account is unlocked and `--mine` is set on the miner node.
- **`genesis hash mismatch`** — delete old chain data and re-run `geth init`.
- **Peer connection issues** — confirm the P2P port (TCP and UDP) is open between the two nodes.
- **`invalid address`** — make sure the address used with `--unlock` / `--miner.etherbase` actually exists in that node's own keystore.

---

## 12. Notes

- This setup uses Ethash/PoW and doesn't require Clique signers.
- The `extraData` and `ethash` fields in `genesis.json` are standard PoW-style fields for this Geth generation.
- The account in `genesis.json` is pre-funded, so mining can begin immediately without waiting for a balance.
- For the actual production launch — systemd services, the RPC/miner port layout, reverse proxy setup for public wallet access — see the quick-start guide.