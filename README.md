# Standalone Ethereum PoW Chain (Geth v1.10.26-stable)

This repository contains a private Ethereum network configuration for running a Proof-of-Work (PoW) chain with Geth 1.10.26-stable. It is designed for a local or private test network and uses Ethash rather than Clique.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Install Geth](#2-install-geth)
3. [Create a Miner Account](#3-create-a-miner-account)
4. [Prepare the Password File](#4-prepare-the-password-file)
5. [Initialize the Genesis](#5-initialize-the-genesis)
6. [Start the Node](#6-start-the-node)
7. [Useful Commands](#7-useful-commands)
8. [Import an Existing Wallet Key](#8-import-an-existing-wallet-key)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Prerequisites

Before starting, make sure you have:

- A Linux or macOS machine
- `git`, `make`, and a compiler toolchain
- Basic terminal experience
- Internet access if you are downloading or building Geth from source

You will need a Geth binary that supports the older Ethereum protocol layout used by this setup. The recommended version is `v1.10.26`.

---

## 2. Install Geth

You have two options.

### Option A: Download a prebuilt binary

Download the Geth 1.10.26 binary for your platform from the official Geth releases page and place it in a directory that is on your `PATH`, such as `/usr/local/bin`.

### Option B: Build from source

Run the following commands:

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

You should see output beginning with `1.10.26`.

> If `geth` is not found, run `which geth` and make sure the binary is installed in your `PATH`.

---

## 3. Create a Miner Account

The node needs an account to receive mining rewards and to serve as the coinbase address.

Run:

```bash
geth account new --datadir ./node1
```

You will be asked to create a password. Choose a strong password and remember it.

The output will include a public address similar to:

```text
Public address of the key: 0x1234567890abcdef1234567890abcdef12345678
```

Save this address because you will use it in the startup command.

---

## 4. Prepare the Password File

Create a password file for non-interactive startup:

```bash
echo "your-password-here" > password.txt
chmod 600 password.txt
```

This file is used by `geth` when unlocking the account for mining.

> Keep this password file private. It contains the password for your local keystore account.

---

## 5. Initialize the Genesis

This repository already contains a genesis file named `genesis.json`.

Initialize the chain with:

```bash
geth init --datadir ./node1 genesis.json
```

Expected result:

```text
Successfully wrote genesis state
```

If you see an error, check that:

- the file path is correct
- the genesis file is valid JSON
- you are using a compatible Geth version

### Important note

If you change `genesis.json` after initialization, delete the old chain data first:

```bash
rm -rf ./node1/geth ./node1/keystore
geth init --datadir ./node1 genesis.json
```

This prevents old chain state from conflicting with the new genesis configuration.

---

## 6. Start the Node

You can run two separate node types.

### Option A: RPC-only node (no password, no wallet, no mining)

Use this if you want a node that serves RPC requests but does not mine.

```bash
geth --datadir ./node1 \
  --networkid 5356 \
  --rpc --rpcaddr 0.0.0.0 --rpcport 8545 \
  --rpcapi eth,net,web3,personal,admin \
  --port 30303 \
  console
```

This is the simplest launch config for RPC access only.

### Option B: Separate mining node (advanced)

Use this for a dedicated mining node that connects to the same chain and mines blocks.

```bash
geth --datadir ./node2 \
  --networkid 5356 \
  --rpc --rpcaddr 0.0.0.0 --rpcport 8546 \
  --rpcapi eth,net,web3,personal,miner,admin \
  --port 30304 \
  --unlock 0xYOUR_ADDRESS \
  --password ./password.txt \
  --miner.etherbase 0xYOUR_ADDRESS \
  --mine \
  --allow-insecure-unlock \
  console
```

Use a separate datadir such as `./node2` for the mining node so it does not share the same node state as the RPC node.

### What each flag does

- `--datadir ./node1` or `./node2` → location of the blockchain data and account keystore
- `--networkid 5356` → must match the `chainId` in `genesis.json`
- `--rpc` → enables the JSON-RPC interface
- `--rpcapi` → enables APIs such as `eth`, `net`, `web3`, `miner`, and `admin`
- `--mine` → starts mining blocks (only used in the mining node)
- `--unlock` → unlocks your account for mining (only used in the mining node)
- `--password` → reads the password from a file (only used in the mining node)
- `--miner.etherbase` → sets the mining reward recipient (only used in the mining node)
- `--allow-insecure-unlock` → allows account unlocking over RPC, useful for local/private networks

---

## 7. Useful Commands

Once the node is running, you can use the console or attach to it with:

```bash
geth attach ./node1/geth.ipc
```

### Basic chain checks

```js
eth.blockNumber
eth.chainId()
eth.getBlock("latest")
```

### Account checks

```js
eth.accounts
eth.getBalance(eth.accounts[0])
web3.fromWei(eth.getBalance(eth.accounts[0]), "ether")
```

### Mining commands

```js
miner.start()
miner.stop()
```

### Networking commands

```js
admin.nodeInfo.enode
admin.peers
net.peerCount
```

---

## 8. Import an Existing Wallet Key

If you already have a wallet private key and want to use it in this network, import it like this:

```bash
echo -n "your_raw_private_key_here" > private_key.txt
echo "your-password-here" > password.txt
chmod 600 password.txt
geth account import --datadir ./node1 --password ./password.txt private_key.txt
rm private_key.txt
```

Then verify it:

```bash
geth account list --datadir ./node1
```

This will create a keystore entry for the imported account.

---

## 9. Troubleshooting

### Common issues

- `Fatal: Error starting protocol stack: authentication needed`  
  Check that the password file exists and the path passed to `--password` is correct.

- `No suitable peers` or no blocks being produced  
  Ensure the node is mining and the account is unlocked.

- `genesis hash mismatch`  
  Delete the old chain data and re-run `geth init`.

- `peer` connection issues  
  Open TCP and UDP port `30303` in your firewall or router.

- `invalid address` or similar account errors  
  Make sure the address you use in `--unlock` and `--miner.etherbase` is a valid account from this datadir.

---

## Notes

- This setup uses Ethash/PoW and does not require Clique signers.
- The `extraData` and `ethash` fields in [genesis.json](genesis.json) are the standard PoW-style fields used by older Geth releases.
- The account in [genesis.json](genesis.json) is pre-funded so the node can begin mining immediately.

