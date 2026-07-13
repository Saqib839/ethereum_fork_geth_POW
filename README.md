# Standalone Ethereum Chain (Geth + Clique PoA)

This repo contains the configuration and setup instructions for running a private, standalone Ethereum-compatible blockchain using `geth` with **Clique Proof-of-Authority** consensus.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Install Geth](#2-install-geth)
3. [Create Signer Account](#3-create-signer-account)
4. [Genesis File Explained](#4-genesis-file-explained)
5. [Generating the `extradata` Field](#5-generating-the-extradata-field)
6. [Initialize the Chain](#6-initialize-the-chain)
7. [Start the Node](#7-start-the-node)
8. [Post-Initialization Commands](#8-post-initialization-commands)
9. [Adding More Nodes / Peers](#9-adding-more-nodes--peers)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Prerequisites

- Ubuntu/Debian server (or any Linux distro)
- `geth` binary installed (see below)
- Python3 (used later to generate `extradata`)
- Basic familiarity with terminal / bash

---

## 2. Install Geth (v1.13.15)

This guide uses **Geth v1.13.15**, as it is one of the last stable releases that supports **Clique Proof of Authority (PoA)**.

### Build from Source

Install the required dependencies:

```bash
sudo apt update
sudo apt install -y golang-go git build-essential
```

Clone the repository and checkout **v1.13.15**:

```bash
git clone https://github.com/ethereum/go-ethereum.git
cd go-ethereum
git checkout v1.13.15
```

Build and install Geth:

```bash
make geth
sudo cp build/bin/geth /usr/local/bin/
```

### Verify Installation

```bash
geth version
```

Expected output:

```text
Geth
Version: 1.13.15-stable
Git Commit: c5ba367eb6232e3eddd7d6226bfd374449c63164
Git Commit Date: 20240417
Architecture: amd64
Go Version: go1.21.6
Operating System: linux
```

> **Note:** Geth **v1.14 and later** removed support for the **Clique** consensus engine. Since this tutorial builds a private Ethereum network using Clique PoA, we use **Geth v1.13.15**. Clique and its deprecation are explained in a later section.

---

## 3. Create Signer Account

Create the account that will sign (mine) blocks under Clique:

```bash
geth account new --datadir ./node1
```

You'll be prompted for a password — save it in a file (e.g. `password.txt`) for later use with `--unlock`.

Output will include your new address, e.g.:
```
Public address of the key:   0xABCDEF1234567890ABCDEF1234567890ABCDEF12
```

**Save this address** — you need it in two places in `genesis.json`: `extradata` and `alloc`.

---

## 4. Genesis File Explained

Example `genesis.json`:

```json
{
  "config": {
    "chainId": 12345,
    "homesteadBlock": 0,
    "eip150Block": 0,
    "eip155Block": 0,
    "eip158Block": 0,
    "byzantiumBlock": 0,
    "constantinopleBlock": 0,
    "petersburgBlock": 0,
    "istanbulBlock": 0,
    "berlinBlock": 0,
    "londonBlock": 0,
    "clique": {
      "period": 5,
      "epoch": 30000
    }
  },
  "difficulty": "1",
  "gasLimit": "8000000",
  "extradata": "0x0000000000000000000000000000000000000000000000000000000000000000ABCDEF1234567890ABCDEF1234567890ABCDEF120000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
  "alloc": {
    "0xABCDEF1234567890ABCDEF1234567890ABCDEF12": {
      "balance": "100000000000000000000000"
    }
  }
}
```

### Field-by-field explanation

| Field | Meaning |
|---|---|
| `chainId` | Unique numeric ID for your network. Prevents transaction replay from other chains (e.g. mainnet=1, Sepolia=11155111). Pick any unused number for a private chain. |
| `homesteadBlock` … `londonBlock` | Ethereum protocol upgrade "activation blocks." Setting all to `0` means all these upgrades are active from block 0 — standard for a new private chain. |
| `clique` | Enables Clique Proof-of-Authority consensus instead of Ethash (PoW) or Beacon (PoS). |
| `clique.period` | Target seconds between blocks (e.g. `5` = a new block every ~5 seconds). |
| `clique.epoch` | Number of blocks between validator-set "checkpoint" resets. `30000` is the common default. |
| `difficulty` | Must be `"1"` for Clique chains (PoA doesn't use difficulty-based mining like PoW). |
| `gasLimit` | Starting gas limit per block. `8000000` is a reasonable default for a private/test chain; can be raised. |
| `extradata` | Encodes the initial Clique signer(s). See detailed breakdown below. |
| `alloc` | Pre-funds specific addresses with an initial balance at genesis (in Wei). `100000000000000000000000` Wei = 100,000 ETH-equivalent. |

---

## 5. Generating the `extradata` Field

Clique's `extradata` has a strict byte structure:

```
0x  +  32 bytes zero padding (vanity)  +  20-byte signer address (no 0x)  +  65 bytes zero padding (seal)
```

Total: `234` hex characters after `0x` (64 + 40 + 130).

**This is the #1 cause of `"can't start clique chain without signers"` errors** — usually because the address was left as a placeholder, mistyped, or the padding lengths are wrong.

### Script to generate it correctly

Save as `gen_extradata.py`:

```python
import sys

def generate_extradata(addresses: list[str]) -> str:
    # normalize and validate
    clean = [a.lower().replace("0x", "") for a in addresses]
    for a in clean:
        if len(a) != 40:
            raise ValueError(f"Invalid address length: {a}")

    # Clique requires signers sorted ascending
    clean_sorted = sorted(clean)

    vanity = "00" * 32
    signers = "".join(clean_sorted)
    seal = "00" * 65
    return "0x" + vanity + signers + seal

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 gen_extradata.py <addr1> <addr2> ... <addrN>")
        sys.exit(1)

    result = generate_extradata(sys.argv[1:])
    expected_len = 64 + (40 * len(sys.argv[1:])) + 130
    print(f"\nSigners: {len(sys.argv[1:])}")
    print(f"Length (should be {expected_len}): {len(result) - 2}")
    print(f"\n{result}\n")

# example usage
# python3 gen_extradata.py 0xAddr1... 0xAddr2... ... 0xAddr20...
```

Run it:
```bash
python3 gen_extradata.py 0xAddr1... 0xAddr2... ... 0xAddr20...
```

Copy the printed value directly into `genesis.json`'s `"extradata"` field.

**Sanity check before running `geth init`:**
```bash
python3 -c "print(len('PASTE_YOUR_EXTRADATA_HERE'.replace('0x','')))"
# Should print 234
```

---

## 6. Initialize the Chain

```bash
geth init --datadir ./node1 genesis.json
```

You should see `Successfully wrote genesis state` (no `Fatal` errors). If you get `can't start clique chain without signers`, revisit Step 5.

> **Note:** If you edit `genesis.json` after already running `init` once, delete the datadir and re-init:
> ```bash
> rm -rf ./node1/geth
> geth init --datadir ./node1 genesis.json
> ```

## 6. If you actually want to use your wallet's existing private key
You need the import command instead, not account new. Here's the correct flow:
1. Get your private key from your wallet

MetaMask: Account menu → Account details → Export private key (you'll need to enter your MetaMask password)
Copy the raw hex key (looks like abc123..., 64 hex characters, with or without 0x prefix)

2. Save it temporarily to a file (no 0x prefix, no quotes, no newline issues)
```bash 
echo -n "your_raw_private_key_here" > private_key.txt
```
3. Create your password file first (so import isn't interactive)
```bash
echo "choose-a-real-password" > password.txt
chmod 600 password.txt
```
4. Import the key using that password
```bash
geth account import --datadir ./node1 --password ./password.txt private_key.txt
```
This encrypts your wallet's private key into a geth keystore file, using the password you just defined.
5. Immediately delete the raw key file
```bash
rm private_key.txt
```
6. Confirm the imported address matches your wallet
```bash
geth account list --datadir ./node1
```
The address shown should be identical to your wallet's address — if so, the import worked correctly and this is the same account you already know from your wallet.

---

## 7. Start the Node

```bash
geth --datadir ./node1 \
  --networkid 12345 \
  --http --http.addr 0.0.0.0 --http.port 8545 \
  --http.api eth,net,web3,personal,clique,admin,miner \
  --port 30303 \
  --unlock 0x4A8b0eA298383Af0D62B572605599d4843fe1c6C \
  --password ./password.txt \
  --miner.etherbase 0x4A8b0eA298383Af0D62B572605599d4843fe1c6C \
  --mine \
  --allow-insecure-unlock \
  console
```
```bash
nohup geth --datadir ./node1 \
  --networkid 12345 \
  --http --http.addr 0.0.0.0 --http.port 8545 \
  --http.api eth,net,web3,personal,clique,admin,miner \
  --port 30303 \
  --unlock 0x4A8b0eA298383Af0D62B572605599d4843fe1c6C \
  --password ./password.txt \
  --miner.etherbase 0x4A8b0eA298383Af0D62B572605599d4843fe1c6C \
  --mine \
  --allow-insecure-unlock \
  > geth.log 2>&1 &
```
nohup ... & keeps it running after you log out; output goes to geth.log.

| Flag | Purpose |
|---|---|
| `--networkid` | Must match `chainId` used in genesis (best practice). |
| `--http.api` | Which RPC namespaces to expose. `clique` is needed to query signer status; `admin` for peer management; `miner` for start/stop mining. |
| `--unlock` + `--password` | Unlocks the signer account non-interactively so it can sign blocks. |
| `--mine` | Enables block production (signing, under Clique). |
| `--allow-insecure-unlock` | Required when unlocking an account while HTTP RPC is exposed — **only use on trusted/private networks**, never on a publicly exposed node. |
| `console` | Drops you into the interactive JS console after starting. |

---

## 8. Post-Initialization Commands

Once you're in the `geth` console (or attach via `geth attach ./node1/geth.ipc`), useful commands:

### Chain / block info
```js
eth.blockNumber                  // current block height
eth.getBlock("latest")           // full latest block details
eth.chainId()                    // confirm chain ID
```

### Accounts
```js
eth.accounts                     // list of accounts on this node
eth.getBalance(eth.accounts[0])  // balance in Wei
web3.fromWei(eth.getBalance(eth.accounts[0]), "ether")  // balance in ETH units
personal.newAccount("password")  // create another account
```

### Mining / signing (Clique)
```js
miner.start()                    // start signing blocks (if not already mining)
miner.stop()                     // stop signing
clique.getSigners()              // list current authorized signers
clique.proposals                 // pending signer add/remove votes
clique.propose("0xNewAddr", true)   // vote to ADD a new signer
clique.propose("0xOldAddr", false)  // vote to REMOVE a signer
clique.status()                  // signer performance/status
```

### Networking / peers
```js
admin.nodeInfo                   // this node's enode URL, ID, ports
admin.peers                      // list connected peers
admin.addPeer("enode://...")     // manually connect to another node
net.peerCount                    // number of connected peers
net.listening                    // true/false
```

### Transactions
```js
eth.sendTransaction({
  from: eth.accounts[0],
  to: "0xRecipientAddress",
  value: web3.toWei(1, "ether")
})
eth.getTransaction("0xTxHash")   // look up tx by hash
eth.getTransactionReceipt("0xTxHash")
```

### Logs / debugging
```js
txpool.status                    // pending/queued tx counts
debug.traceTransaction("0xTxHash")  // detailed execution trace
```

### Shutting down cleanly
```js
exit
```
or from another terminal:
```bash
geth attach ./node1/geth.ipc --exec "admin.stopRPC()"
```

---

## 9. Adding More Nodes / Peers

On a second machine/directory, repeat Steps 3–6 using the **same `genesis.json`**, then:

```bash
# On node1 console — get enode address
admin.nodeInfo.enode

# On node2 console — connect to node1
admin.addPeer("enode://<node1-id>@<node1-ip>:30303")
```

To make a second node a Clique signer too, its address must first be added via `clique.propose()` from an existing signer, and a majority of existing signers must approve it (standard Clique governance).

---

## 10. Troubleshooting

| Error | Likely Cause |
|---|---|
| `can't start clique chain without signers` | `extradata` missing/malformed — see Step 5 |
| `genesis hash mismatch` | Genesis file changed after `init` without wiping datadir |
| `no signer to authorize` (won't mine) | Account not unlocked, or unlocked account isn't in the signer set |
| Node not syncing/peering | Check firewall on `30303` (TCP+UDP), verify `admin.addPeer` enode string is correct |
| `Fatal: Error starting protocol stack: authentication needed` | Password file path wrong or empty in `--password` |

---

## Quick Reference: File Layout

```
ethereum_fork_geth/
├── genesis.json
├── password.txt
├── gen_extradata.py
└── node1/
    ├── geth/           # chain data (created by `geth init`)
    └── keystore/       # account keys (created by `geth account new`)
```


# Troubleshoot

## Password.txt testing
```bash
geth account list --datadir ./node1
```
Note the address, then test:
```bash
echo "" > password.txt
geth --datadir ./node1 --unlock 0xYourAddress --password ./password.txt console
```

