# Nakamoto Coefficient Chain — Complete Setup Guide

> Private two-node Ethereum PoW blockchain — Nakamoto Coefficient Chain
> Built and running on Ubuntu 24.04 server at `45.249.8.94`
> Geth v1.10.26 (pre-Merge, Ethash PoW) | Chain ID: 5356 | Coin: NKM

---

## Table of Contents

1. [Chain Identity](#1-chain-identity)
2. [Repository Structure](#2-repository-structure)
3. [Current Account Info](#3-current-account-info)
4. [Deployed Contracts — Uniswap V3 DEX](#4-deployed-contracts--uniswap-v3-dex)
5. [MetaMask Configuration](#5-metamask-configuration)
6. [Software Versions](#6-software-versions)
7. [Fresh Install — Step by Step](#7-fresh-install--step-by-step)
8. [genesis.json — Rules and Structure](#8-genesisjson--rules-and-structure)
9. [Starting the Nodes](#9-starting-the-nodes)
10. [Connecting the Nodes](#10-connecting-the-nodes)
11. [RPC Commands Reference](#11-rpc-commands-reference)
12. [Monitoring Commands](#12-monitoring-commands)
13. [Common Errors and Fixes](#13-common-errors-and-fixes)
14. [Port Reference](#14-port-reference)
15. [Useful References](#15-useful-references)

---

## 1. Chain Identity

| Property | Value |
|----------|-------|
| Chain Name | Nakamoto Coefficient |
| Chain ID | `5356` |
| Chain ID (hex) | `0x14EC` |
| Coin Name | Nakamoto Coin |
| Coin Symbol | `NKM` |
| Coin Decimals | `18` (EVM standard — cannot be changed) |
| Initial Supply | `20,000,000 NKM` (pre-mined to miner wallet) |
| Block Reward | `2 NKM` per block (Ethash ConstantinopleBlockReward) |
| Block Time | ~10-20 seconds (auto-adjusted by difficulty) |
| Gas Limit | `30,000,000` per block (0x1C9C380 — same as ETH mainnet) |
| Consensus | Ethash Proof of Work |
| Server IP | `45.249.8.94` |
| Node1 RPC | `http://45.249.8.94:8545` (miner, internal) |
| Node2 RPC | `http://45.249.8.94:8546` (public RPC) |

> ℹ️ **Why 18 decimals?** The EVM is hardwired to use 18 decimals for native coins. Changing this would break MetaMask, ethers.js, Hardhat, Uniswap V3 math, and every other EVM tool. All EVM chains use 18 decimals internally — the symbol displayed is just cosmetic.

---

## 2. Repository Structure

```
~/ (home: /home/ovextech)
├── go-ethereum-pow/              ← Geth v1.10.26 source code (cloned + built here)
│   └── build/bin/geth            ← compiled Geth binary
│
├── Uniswap_Dex_Deployment/       ← Uniswap V3 deployment repo
│   ├── .env                      ← chain config for deployment
│   ├── ignition/deployments/
│   │   └── myNewChain-5356.json  ← deployed contract addresses
│   └── contracts/
│       └── WETH9.sol             ← wrapped native coin contract
│
└── ethereum-pow-blockchain/      ← chain data
    ├── genesis.json              ← chain configuration (shared by both nodes)
    ├── node1.log                 ← miner node live logs
    ├── node2.log                 ← rpc node live logs
    ├── node1/                    ← MINER node (port 8545)
    │   ├── geth/                 ← chain database (delete to reinit)
    │   ├── keystore/             ← ⚠️ NEVER DELETE — contains accounts
    │   └── geth.ipc              ← IPC socket (appears when node running)
    └── node2/                    ← RPC node (port 8546)
        ├── geth/
        ├── keystore/
        └── geth.ipc
```

---

## 3. Current Account Info

### Node1 — Miner Account

| Field | Value |
|-------|-------|
| Public Address | `0x80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2` |
| Private Key | `0x8fd14eaa99bf3e15c56f9bc45cea1b9bbce8fc35dc70d984d10a027462280ed8` |
| Keystore File | `node1/keystore/UTC--2026-07-23T19-09-47.194076365Z--80a63d2c5cb3d83e3ea235c98cd64710c43e1ef2` |
| Password | `p1@1234` |
| Role | Mining rewards go here — also used to deploy contracts |
| Pre-funded | Yes — 20,000,000 NKM in genesis alloc |

### Node2 — RPC Account

| Field | Value |
|-------|-------|
| Public Address | `0x7cc201Dcd87Dbbe7762b8Db914367D27478202e0` |
| Keystore File | `node2/keystore/UTC--2026-07-23T19-19-55.210441037Z--7cc201dcd87dbbe7762b8db914367d27478202e0` |
| Role | RPC endpoint only, not mining |

### Node1 Enode (current — changes on fresh start)

```
enode://ea8ec493fc81c03770af9021bc8147921270c6fd13536db9c71c0244746eda26969d9fd1da553a4365d7d1c313f17e9005026c369c004ab1472be718138624c9@127.0.0.1:30303
```

> ⚠️ **CRITICAL**: Never commit private keys to git. Never share them. Back up the keystore directory separately.

> ⚠️ The enode key changes if you delete `node1/geth`. After any reinit, get the new enode via:
> ```bash
> ~/go-ethereum-pow/build/bin/geth attach ~/ethereum-pow-blockchain/node1/geth.ipc
> admin.nodeInfo.enode
> ```

---

## 4. Deployed Contracts — Uniswap V3 DEX

All deployed on chain ID `5356`. Deployment record:
`~/Uniswap_Dex_Deployment/ignition/deployments/myNewChain-5356.json`

| Contract | Address |
|----------|---------|
| WETH9 (Wrapped NKM) | `0x55E0C3d36DcD26f8f0fE738799a6B41728AcE9AF` |
| UniswapV3Factory | `0x20b5d680A19868842991BA3b89F4399dAB8E32D6` |
| NFTDescriptor | `0xb0f35c597579A73cb9d0620588975a31B04087Ad` |
| NonfungibleTokenPositionDescriptor | `0x5c0dffF18De91C4826b4670F67164D9707cC4E86` |
| NonfungiblePositionManager | `0xcb2d87e18e82ea62ee45e41F8B65A3362D5564bB` |
| SwapRouter | `0xe6f89767D7ee7d6f9824a1e36ed2C2a25a784672` |
| QuoterV2 | `0x0C865AC3cC9F11718d911ca9b52d6c31b8369671` |

### Verify a contract is on chain

```bash
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_getCode","params":["0x55E0C3d36DcD26f8f0fE738799a6B41728AcE9AF","latest"],"id":1}'
# Returns long bytecode = contract exists
# Returns "0x" = no contract at that address
```

### Redeploy contracts (after chain reset)

```bash
cd ~/Uniswap_Dex_Deployment
npm run deploy:chain
```

---

## 5. MetaMask Configuration

Add the Nakamoto Coefficient chain to MetaMask:

| Field | Value |
|-------|-------|
| Network Name | Nakamoto Coefficient |
| RPC URL | `http://45.249.8.94:8546` |
| Chain ID | `5356` |
| Currency Symbol | `NKM` |
| Block Explorer URL | (leave blank — not set up yet) |

> ⚠️ Node2 must be started with `--http.corsdomain "*"` and `--http.vhosts "*"` flags for MetaMask to connect. See Section 9.

### Test RPC is reachable from outside

Run this from your local machine (not the server):

```bash
curl -s -X POST http://45.249.8.94:8546 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'
# Expected: {"result":"0x14ec"}
```

---

## 6. Software Versions

| Software | Version | Why This Version |
|----------|---------|-----------------|
| Ubuntu | 24.04 LTS | Server OS |
| Go | 1.21.13 | Compatible with Geth v1.10.26 |
| Geth | v1.10.26 | Last pre-Merge version — keeps Ethash PoW |
| Node.js | 22.x | Required by Uniswap deployment repo (>=20 <25) |
| Consensus | Ethash (PoW) | No Beacon client needed |

> ⚠️ **Do NOT use Geth v1.11+** — those versions require a Beacon consensus client and will not mine with Ethash alone.

---

## 7. Fresh Install — Step by Step

Follow this section exactly if rebuilding from scratch on a new server.

### 7.1 — System packages

```bash
sudo apt update
sudo apt install -y build-essential git wget python3 python3-venv
```

### 7.2 — Fix DNS if needed

```bash
# If wget/git fail with DNS errors:
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
ping -c 2 google.com
```

### 7.3 — Install Go 1.21.13

```bash
wget https://go.dev/dl/go1.21.13.linux-amd64.tar.gz
sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xzf go1.21.13.linux-amd64.tar.gz

echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc

go version
# Expected: go version go1.21.13 linux/amd64
```

### 7.4 — Install Node.js 22

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
node --version   # must be v22.x.x
```

### 7.5 — Clone and build Geth v1.10.26 from source

```bash
git clone https://github.com/ethereum/go-ethereum.git go-ethereum-pow
cd go-ethereum-pow
git checkout v1.10.26
git describe --tags    # must print: v1.10.26
make geth
./build/bin/geth version
```

### 7.6 — Create project structure

```bash
mkdir -p ~/ethereum-pow-blockchain/node1
mkdir -p ~/ethereum-pow-blockchain/node2
```

### 7.7 — Create genesis.json

```bash
cat > ~/ethereum-pow-blockchain/genesis.json << 'EOF'
{
  "config": {
    "chainId": 5356,
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
    "ethash": {}
  },
  "difficulty": "0x400",
  "gasLimit": "0x1C9C380",
  "extraData": "0x0000000000000000000000000000000000000000000000000000000000000000",
  "alloc": {
    "80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2": {
      "balance": "20000000000000000000000000"
    }
  }
}
EOF
```

### 7.8 — Create miner account (node1)

```bash
GETH=~/go-ethereum-pow/build/bin/geth
$GETH account new --datadir ~/ethereum-pow-blockchain/node1
```

Note the public address. Extract the private key:

```bash
python3 -m venv ~/eth-venv
~/eth-venv/bin/pip install eth-account --quiet

cat > /tmp/extract_key.py << 'PYEOF'
import json, os, glob
from eth_account import Account

keystore_dir = os.path.expanduser("~/ethereum-pow-blockchain/node1/keystore")
files = glob.glob(f"{keystore_dir}/UTC--*")
keystore_file = files[0]
print(f"Keystore: {keystore_file}")
with open(keystore_file) as f:
    keystore = json.load(f)
password = input("Enter password: ")
private_key = Account.decrypt(keystore, password)
print(f"\nPublic address : 0x{keystore['address']}")
print(f"Private key    : 0x{private_key.hex()}")
PYEOF

~/eth-venv/bin/python3 /tmp/extract_key.py
```

### 7.9 — Create RPC account (node2)

```bash
$GETH account new --datadir ~/ethereum-pow-blockchain/node2
```

### 7.10 — Initialize both nodes

```bash
GETH=~/go-ethereum-pow/build/bin/geth
$GETH --datadir ~/ethereum-pow-blockchain/node1 init ~/ethereum-pow-blockchain/genesis.json
$GETH --datadir ~/ethereum-pow-blockchain/node2 init ~/ethereum-pow-blockchain/genesis.json
```

Both must print `Successfully wrote genesis state` with the **same hash**.

### 7.11 — Clone and deploy Uniswap V3

```bash
git clone https://github.com/OrbitOne-Finance/Uniswap_Dex_Deployment.git
cd Uniswap_Dex_Deployment
npm ci

cat > .env << 'EOF'
MYNEWCHAIN_URL=http://127.0.0.1:8545
MYNEWCHAIN_CHAIN_ID=5356
MYNEWCHAIN_PRIVATE_KEY=0x8fd14eaa99bf3e15c56f9bc45cea1b9bbce8fc35dc70d984d10a027462280ed8
NATIVE_CURRENCY_SYMBOL=NKM
DEPLOY_CONFIRMATIONS=1
EOF

npm run check       # run tests first
npm run deploy:chain  # deploy to your chain
```

---

## 8. genesis.json — Rules and Structure

Current genesis.json for Nakamoto Coefficient Chain:

```json
{
  "config": {
    "chainId": 5356,            ← Nakamoto Coefficient chain ID
    "homesteadBlock": 0,        ← all EVM upgrades active from block 0
    "eip150Block": 0,
    "eip155Block": 0,
    "eip158Block": 0,
    "byzantiumBlock": 0,
    "constantinopleBlock": 0,
    "petersburgBlock": 0,
    "istanbulBlock": 0,
    "berlinBlock": 0,
    "londonBlock": 0,
    "ethash": {}                ← ✅ REQUIRED — Ethash PoW consensus
  },
  "difficulty": "0x400",        ← low = fast blocks (10-20s)
  "gasLimit": "0x1C9C380",      ← 30M gas per block (same as ETH mainnet)
  "extraData": "0x000...000",   ← exactly 32 zero bytes
  "alloc": {
    "80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2": {
      "balance": "20000000000000000000000000"   ← 20M NKM in Wei
    }
  }
}
```

### What NOT to include

| Field | Why to exclude |
|-------|---------------|
| `"terminalTotalDifficulty": 0` | Triggers the Merge — chain becomes PoS |
| `"terminalTotalDifficulty": any` | Same problem |
| `"mergeNetsplitBlock"` | Merge-related, avoid |
| `"shanghaiTime"` | Post-merge, not compatible with v1.10.26 |

### Alloc address rules

```json
✅ CORRECT — no 0x, address in quotes:
"alloc": { "80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2": { "balance": "20000000000000000000000000" } }

❌ WRONG — 0x prefix not allowed:
"alloc": { "0x80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2": { ... } }
```

### Balance values

| Amount | Wei value |
|--------|-----------|
| 1 NKM | `1000000000000000000` |
| 1,000 NKM | `1000000000000000000000` |
| 1,000,000 NKM | `1000000000000000000000000` |
| 20,000,000 NKM | `20000000000000000000000000` |

### Reinitializing after genesis changes

```bash
# Stop nodes first
sudo pkill -f geth && sleep 2

# Delete chain database only — NEVER delete keystore
rm -rf ~/ethereum-pow-blockchain/node1/geth
rm -rf ~/ethereum-pow-blockchain/node2/geth

# Re-init both
GETH=~/go-ethereum-pow/build/bin/geth
$GETH --datadir ~/ethereum-pow-blockchain/node1 init ~/ethereum-pow-blockchain/genesis.json
$GETH --datadir ~/ethereum-pow-blockchain/node2 init ~/ethereum-pow-blockchain/genesis.json
```

---

## 9. Starting the Nodes

Both nodes run in the background using `nohup`. Logs go to files.

### Kill everything and free all ports first

```bash
sudo pkill -f geth
sleep 2
sudo fuser -k 8545/tcp 2>/dev/null
sudo fuser -k 8546/tcp 2>/dev/null
sudo fuser -k 30303/tcp 2>/dev/null
sudo fuser -k 30304/tcp 2>/dev/null

# Verify all clear
sudo ss -tlnp | grep -E '8545|8546|30303|30304'
```

### Start node1 — Miner

```bash
nohup ~/go-ethereum-pow/build/bin/geth \
  --datadir ~/ethereum-pow-blockchain/node1 \
  --networkid 5356 \
  --port 30303 \
  --http \
  --http.addr 0.0.0.0 \
  --http.port 8545 \
  --http.api admin,eth,miner,net,web3,personal \
  --http.corsdomain "*" \
  --http.vhosts "*" \
  --allow-insecure-unlock \
  --mine \
  --miner.threads 1 \
  --miner.etherbase "0x80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2" \
  --unlock "0x80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2" \
  --password <(echo "p1@1234") \
  > ~/ethereum-pow-blockchain/node1.log 2>&1 &

echo "Node1 PID: $!"
```

### Start node2 — RPC (public-facing)

> ⚠️ `--authrpc.port 8552` is required — node1 already uses default auth port 8551.
> ⚠️ `--http.corsdomain "*"` and `--http.vhosts "*"` are required for MetaMask to connect.
> ⚠️ Update the enode if node1 was restarted — get fresh enode from `admin.nodeInfo.enode`.

```bash
nohup ~/go-ethereum-pow/build/bin/geth \
  --datadir ~/ethereum-pow-blockchain/node2 \
  --networkid 5356 \
  --port 30304 \
  --http \
  --http.addr 0.0.0.0 \
  --http.port 8546 \
  --http.api admin,eth,net,web3,personal \
  --http.corsdomain "*" \
  --http.vhosts "*" \
  --authrpc.port 8552 \
  --bootnodes "enode://ea8ec493fc81c03770af9021bc8147921270c6fd13536db9c71c0244746eda26969d9fd1da553a4365d7d1c313f17e9005026c369c004ab1472be718138624c9@127.0.0.1:30303" \
  > ~/ethereum-pow-blockchain/node2.log 2>&1 &

echo "Node2 PID: $!"
```

### Check logs anytime

```bash
tail -f ~/ethereum-pow-blockchain/node1.log
tail -f ~/ethereum-pow-blockchain/node2.log
# Ctrl+C to stop
```

---

## 10. Connecting the Nodes

The `--bootnodes` flag connects automatically. If node2 shows 0 peers after 30 seconds:

```bash
# Step 1: get fresh enode from node1
~/go-ethereum-pow/build/bin/geth attach ~/ethereum-pow-blockchain/node1/geth.ipc
# Inside console:
admin.nodeInfo.enode
# Copy the output, then:
exit

# Step 2: add peer to node2 manually
~/go-ethereum-pow/build/bin/geth attach ~/ethereum-pow-blockchain/node2/geth.ipc
# Inside console — paste YOUR enode with 127.0.0.1:
admin.addPeer("enode://PASTE_NODE1_ENODE_HERE@127.0.0.1:30303")
# Verify:
admin.peers   # should show node1
exit
```

> ⚠️ Always use `127.0.0.1` (not the public IP) in the enode when both nodes are on the same server.

---

## 11. RPC Commands Reference

All commands work as curl HTTP calls. Node1 = port `8545`, Node2 = port `8546`.

### Format

```bash
curl -s -X POST http://127.0.0.1:PORT \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"METHOD","params":[PARAMS],"id":1}'
```

---

### Block and Chain Info

```bash
# Current block number
curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# Chain ID (returns 0x14ec = 5356)
curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'

# Latest block full info
curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["latest", false],"id":1}'

# Specific block by number (e.g. block 1)
curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["0x1", false],"id":1}'

# Block by hash
curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_getBlockByHash","params":["0xBLOCK_HASH", false],"id":1}'

# Gas price
curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_gasPrice","params":[],"id":1}'

# Tx count in latest block
curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_getBlockTransactionCountByNumber","params":["latest"],"id":1}'
```

### Account and Balance

```bash
# NKM balance of miner (returns Wei hex — divide by 10^18 for NKM)
curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_getBalance","params":["0x80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2","latest"],"id":1}'

# Nonce (transaction count) of an address
curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_getTransactionCount","params":["0x80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2","latest"],"id":1}'

# Check if address is a contract (returns 0x if not)
curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_getCode","params":["0xCONTRACT_ADDRESS","latest"],"id":1}'
```

### Mining and Network

```bash
# Is node1 mining?
curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_mining","params":[],"id":1}'

# Miner hashrate
curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_hashrate","params":[],"id":1}'

# Coinbase (miner address)
curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_coinbase","params":[],"id":1}'

# Peer count on node2
curl -s -X POST http://127.0.0.1:8546 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"net_peerCount","params":[],"id":1}'

# Network ID
curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"net_version","params":[],"id":1}'

# Sync status (false = fully synced)
curl -s -X POST http://127.0.0.1:8546 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_syncing","params":[],"id":1}'

# Geth client version
curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"web3_clientVersion","params":[],"id":1}'
```

### Transactions

```bash
# Send signed raw transaction
curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_sendRawTransaction","params":["0xSIGNED_TX_HEX"],"id":1}'

# Get transaction by hash
curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_getTransactionByHash","params":["0xTX_HASH"],"id":1}'

# Get transaction receipt (null = not mined yet)
curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_getTransactionReceipt","params":["0xTX_HASH"],"id":1}'

# Estimate gas
curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_estimateGas","params":[{"from":"0x80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2","to":"0x7cc201Dcd87Dbbe7762b8Db914367D27478202e0","value":"0xDE0B6B3A7640000"}],"id":1}'

# Call contract read function (no gas)
curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_call","params":[{"to":"0xCONTRACT_ADDRESS","data":"0xFUNCTION_SELECTOR"},"latest"],"id":1}'
```

### Logs and Events

```bash
# Get all logs from a contract
curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_getLogs","params":[{"fromBlock":"0x0","toBlock":"latest","address":"0xCONTRACT_ADDRESS"}],"id":1}'
```

### IPC Console (attach directly to node)

```bash
# Attach to node1
~/go-ethereum-pow/build/bin/geth attach ~/ethereum-pow-blockchain/node1/geth.ipc

# Attach to node2
~/go-ethereum-pow/build/bin/geth attach ~/ethereum-pow-blockchain/node2/geth.ipc
```

Inside the console:

```javascript
eth.blockNumber                                          // current block
eth.mining                                               // is mining?
eth.hashrate                                             // hash/sec
eth.coinbase                                             // miner address
eth.getBalance("0xADDRESS")                             // balance in Wei
web3.fromWei(eth.getBalance("0xADDRESS"), "ether")      // balance in NKM
eth.getBlock("latest")                                   // latest block
eth.getBlock(5)                                          // block #5
eth.getTransaction("0xTX_HASH")                          // tx details
eth.getTransactionReceipt("0xTX_HASH")                  // tx receipt
net.peerCount                                            // peer count
admin.peers                                              // peer details
admin.nodeInfo.enode                                     // this node's enode
miner.start(1)                                           // start mining
miner.stop()                                             // stop mining
miner.setEtherbase("0xADDRESS")                         // set reward address
personal.listAccounts                                    // list accounts
personal.unlockAccount("0xADDR", "pass", 0)             // unlock forever
```

---

## 12. Monitoring Commands

### Live dashboard (refreshes every 5 seconds)

```bash
watch -n 5 '
echo "=== $(date) ===" &&
echo -n "Node1 block : " && curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" --data "{\"jsonrpc\":\"2.0\",\"method\":\"eth_blockNumber\",\"params\":[],\"id\":1}" | grep -o "0x[^\"]*" &&
echo -n "Node1 mining: " && curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" --data "{\"jsonrpc\":\"2.0\",\"method\":\"eth_mining\",\"params\":[],\"id\":1}" | grep -o "true\|false" &&
echo -n "Node2 block : " && curl -s -X POST http://127.0.0.1:8546 -H "Content-Type: application/json" --data "{\"jsonrpc\":\"2.0\",\"method\":\"eth_blockNumber\",\"params\":[],\"id\":1}" | grep -o "0x[^\"]*" &&
echo -n "Node2 peers : " && curl -s -X POST http://127.0.0.1:8546 -H "Content-Type: application/json" --data "{\"jsonrpc\":\"2.0\",\"method\":\"net_peerCount\",\"params\":[],\"id\":1}" | grep -o "0x[^\"]*" &&
echo -n "Miner NKM   : " && curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" --data "{\"jsonrpc\":\"2.0\",\"method\":\"eth_getBalance\",\"params\":[\"0x80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2\",\"latest\"],\"id\":1}" | grep -o "0x[^\"]*"
'
```

### Quick one-time status check

```bash
echo "=== Node1 ===" && \
curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' && echo "" && \
echo "=== Node2 ===" && \
curl -s -X POST http://127.0.0.1:8546 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' && echo "" && \
echo "=== Node2 Peers ===" && \
curl -s -X POST http://127.0.0.1:8546 -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"net_peerCount","params":[],"id":1}'
```

### Watch logs live

```bash
tail -f ~/ethereum-pow-blockchain/node1.log   # miner
tail -f ~/ethereum-pow-blockchain/node2.log   # rpc
```

### Check processes are running

```bash
ps aux | grep geth | grep -v grep
```

---

## 13. Common Errors and Fixes

### Error: `No such file or directory` for geth binary
Repo cloned with different name. Correct path: `~/go-ethereum-pow/build/bin/geth`

### Error: Bootstrap URL invalid / missing 'enr:' prefix
Used placeholder instead of real enode. Must paste actual enode string from `admin.nodeInfo.enode`.

### Error: `listen tcp 127.0.0.1:8551: bind: address already in use`
Both nodes default to auth port 8551. Add `--authrpc.port 8552` to node2 only.

### Error: `HTTP server graceful shutdown timed out`
Port still occupied by previous instance:
```bash
sudo fuser -k 8546/tcp 2>/dev/null
sudo fuser -k 30304/tcp 2>/dev/null
```

### Error: `Consensus: Beacon` instead of `Consensus: Ethash`
`terminalTotalDifficulty` is in genesis.json. Remove it, delete geth databases, reinit.

### Error: `eth.blockNumber` stuck at 0
DAG still generating. Check:
```bash
grep "Generating DAG" ~/ethereum-pow-blockchain/node1.log | tail -5
```
Wait until `percentage=100`.

### Error: Different genesis hashes on node1 and node2
genesis.json changed between inits. Delete both geth dirs and reinit together.

### Error: `externally-managed-environment` on pip
```bash
python3 -m venv ~/eth-venv
~/eth-venv/bin/pip install eth-account
~/eth-venv/bin/python3 /tmp/script.py
```

### Error: `EOF when reading a line` in Python
Don't use heredoc for interactive scripts. Save to file first:
```bash
cat > /tmp/script.py << 'PYEOF'
# content
PYEOF
~/eth-venv/bin/python3 /tmp/script.py
```

### Error: Node2 shows 0 peers
Enode changed after node1 restart. Get fresh enode and addPeer manually:
```bash
~/go-ethereum-pow/build/bin/geth attach ~/ethereum-pow-blockchain/node1/geth.ipc
# admin.nodeInfo.enode → copy result → exit
~/go-ethereum-pow/build/bin/geth attach ~/ethereum-pow-blockchain/node2/geth.ipc
# admin.addPeer("enode://FRESH_ENODE@127.0.0.1:30303")
```

### Error: MetaMask can't connect to RPC
Node2 missing CORS flags. Restart with `--http.corsdomain "*" --http.vhosts "*"`.

### Chain accidentally started as mainnet
```bash
rm -rf ~/.ethereum && rm -rf ~/.ethash
# Always use --datadir flag
```

---

## 14. Port Reference

| Node | Role | P2P Port | RPC Port | Auth RPC Port |
|------|------|----------|----------|---------------|
| node1 | Miner (internal) | 30303 | 8545 | 8551 (default) |
| node2 | RPC (public) | 30304 | 8546 | 8552 (custom) |

---

## 15. Useful References

| Resource | URL |
|----------|-----|
| Geth v1.10.26 release | https://github.com/ethereum/go-ethereum/releases/tag/v1.10.26 |
| Go 1.21.13 download | https://go.dev/dl/go1.21.13.linux-amd64.tar.gz |
| Geth JSON-RPC API | https://geth.ethereum.org/docs/interacting-with-geth/rpc |
| JSON-RPC spec | https://ethereum.org/en/developers/docs/apis/json-rpc |
| Uniswap V3 Deployment Repo | https://github.com/OrbitOne-Finance/Uniswap_Dex_Deployment |

---

## Quick Start (everything already built and initialized)

```bash
# Kill any existing geth
sudo pkill -f geth && sleep 2

# Start node1 (miner)
nohup ~/go-ethereum-pow/build/bin/geth \
  --datadir ~/ethereum-pow-blockchain/node1 \
  --networkid 5356 --port 30303 \
  --http --http.addr 0.0.0.0 --http.port 8545 \
  --http.api admin,eth,miner,net,web3,personal \
  --http.corsdomain "*" --http.vhosts "*" \
  --allow-insecure-unlock --mine --miner.threads 1 \
  --miner.etherbase "0x80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2" \
  --unlock "0x80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2" \
  --password <(echo "p1@1234") \
  > ~/ethereum-pow-blockchain/node1.log 2>&1 &

sleep 3

# Start node2 (RPC) — update enode if node1 was reinstalled
nohup ~/go-ethereum-pow/build/bin/geth \
  --datadir ~/ethereum-pow-blockchain/node2 \
  --networkid 5356 --port 30304 \
  --http --http.addr 0.0.0.0 --http.port 8546 \
  --http.api admin,eth,net,web3,personal \
  --http.corsdomain "*" --http.vhosts "*" \
  --authrpc.port 8552 \
  --bootnodes "enode://ea8ec493fc81c03770af9021bc8147921270c6fd13536db9c71c0244746eda26969d9fd1da553a4365d7d1c313f17e9005026c369c004ab1472be718138624c9@127.0.0.1:30303" \
  > ~/ethereum-pow-blockchain/node2.log 2>&1 &

sleep 8

# Verify
echo "Node1 mining:" && curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" --data '{"jsonrpc":"2.0","method":"eth_mining","params":[],"id":1}'
echo ""
echo "Chain ID:" && curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" --data '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'
echo ""
echo "Node2 peers:" && curl -s -X POST http://127.0.0.1:8546 -H "Content-Type: application/json" --data '{"jsonrpc":"2.0","method":"net_peerCount","params":[],"id":1}'
```
