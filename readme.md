# Ethereum PoW Private Blockchain — Complete Setup Guide

> Private two-node Ethereum blockchain using Geth v1.10.26 (pre-Merge, Ethash PoW)
> Built and running on Ubuntu 24.04 server at `45.249.8.94`

---

## Table of Contents

1. [Repository Structure](#1-repository-structure)
2. [Current Account Info](#2-current-account-info)
3. [Software Versions](#3-software-versions)
4. [Fresh Install — Step by Step](#4-fresh-install--step-by-step)
5. [genesis.json — Rules and Structure](#5-genesisjson--rules-and-structure)
6. [Starting the Nodes](#6-starting-the-nodes)
7. [Connecting the Nodes](#7-connecting-the-nodes)
8. [RPC Commands Reference](#8-rpc-commands-reference)
9. [Monitoring Commands](#9-monitoring-commands)
10. [Common Errors and Fixes](#10-common-errors-and-fixes)
11. [Port Reference](#11-port-reference)
12. [Useful References](#12-useful-references)

---

## 1. Repository Structure

```
~/ (home: /home/ovextech)
├── go-ethereum-pow/              ← Geth source code (cloned + built here)
│   └── build/bin/geth            ← compiled Geth binary
│
└── ethereum-pow-blockchain/      ← your private chain data
    ├── genesis.json              ← chain configuration (shared by both nodes)
    ├── node1.log                 ← miner node live logs
    ├── node2.log                 ← rpc node live logs
    ├── node1/                    ← MINER node
    │   ├── geth/                 ← chain database (can be deleted to reinit)
    │   ├── keystore/             ← ⚠️ NEVER DELETE — contains your accounts
    │   └── geth.ipc              ← IPC socket (appears when node is running)
    └── node2/                    ← RPC node
        ├── geth/
        ├── keystore/
        └── geth.ipc
```

---

## 2. Current Account Info

### Node1 — Miner Account

| Field | Value |
|-------|-------|
| Public Address | `0x80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2` |
| Private Key | `0x8fd14eaa99bf3e15c56f9bc45cea1b9bbce8fc35dc70d984d10a027462280ed8` |
| Keystore File | `node1/keystore/UTC--2026-07-23T19-09-47.194076365Z--80a63d2c5cb3d83e3ea235c98cd64710c43e1ef2` |
| Password | `p1@1234` |
| Role | Mining rewards go here |
| Pre-funded | Yes — 1,000,000 ETH in genesis alloc |

### Node2 — RPC Account

| Field | Value |
|-------|-------|
| Public Address | `0x7cc201Dcd87Dbbe7762b8Db914367D27478202e0` |
| Keystore File | `node2/keystore/UTC--2026-07-23T19-19-55.210441037Z--7cc201dcd87dbbe7762b8db914367d27478202e0` |
| Role | RPC endpoint, not mining |

> ⚠️ **CRITICAL**: Never commit private keys to git. Never share them. Back up the keystore directory separately.

---

## 3. Software Versions

| Software | Version | Why This Version |
|----------|---------|-----------------|
| Ubuntu | 24.04 LTS | Server OS |
| Go | 1.21.13 | Compatible with Geth v1.10.26 |
| Geth | v1.10.26 | Last pre-Merge version — keeps Ethash PoW |
| Consensus | Ethash (PoW) | No Beacon client needed |

> ⚠️ **Do NOT use Geth v1.11+** — those versions expect a Beacon consensus client and will not mine with Ethash alone.

---

## 4. Fresh Install — Step by Step

Follow this section exactly if rebuilding from scratch.

### 4.1 — System packages

```bash
sudo apt update
sudo apt install -y build-essential git wget python3 python3-venv
```

### 4.2 — Install Go 1.21.13

```bash
wget https://go.dev/dl/go1.21.13.linux-amd64.tar.gz
sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xzf go1.21.13.linux-amd64.tar.gz

echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc

go version
# Expected: go version go1.21.13 linux/amd64
```

> ⚠️ If `wget` fails with DNS error, fix DNS first:
> ```bash
> echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
> ping -c 2 google.com   # verify it works
> ```

### 4.3 — Clone Geth and checkout v1.10.26

```bash
git clone https://github.com/ethereum/go-ethereum.git go-ethereum-pow
cd go-ethereum-pow
git checkout v1.10.26
git describe --tags    # must print: v1.10.26
```

### 4.4 — Build Geth from source

```bash
cd ~/go-ethereum-pow
make geth

# Verify binary exists and works
./build/bin/geth version
```

### 4.5 — Create project structure

```bash
mkdir -p ~/ethereum-pow-blockchain/node1
mkdir -p ~/ethereum-pow-blockchain/node2
cd ~/ethereum-pow-blockchain
```

### 4.6 — Create genesis.json

```bash
cat > ~/ethereum-pow-blockchain/genesis.json << 'EOF'
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
    "ethash": {}
  },
  "difficulty": "0x400",
  "gasLimit": "0x8000000",
  "extraData": "0x0000000000000000000000000000000000000000000000000000000000000000",
  "alloc": {}
}
EOF
```

### 4.7 — Create miner account (node1)

```bash
GETH=~/go-ethereum-pow/build/bin/geth
$GETH account new --datadir ~/ethereum-pow-blockchain/node1
```

Note the public address printed. Then extract the private key:

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

Save both values securely before continuing.

### 4.8 — Update genesis.json with miner alloc

Replace `YOUR_ADDRESS_WITHOUT_0x` with the actual address (no `0x` prefix):

```bash
python3 -c "
import json
with open('/home/ovextech/ethereum-pow-blockchain/genesis.json') as f:
    g = json.load(f)
g['alloc'] = {'YOUR_ADDRESS_WITHOUT_0x': {'balance': '1000000000000000000000000'}}
with open('/home/ovextech/ethereum-pow-blockchain/genesis.json', 'w') as f:
    json.dump(g, f, indent=2)
print('Done')
"
```

### 4.9 — Create RPC account (node2)

```bash
$GETH account new --datadir ~/ethereum-pow-blockchain/node2
```

### 4.10 — Initialize both nodes

```bash
GETH=~/go-ethereum-pow/build/bin/geth

$GETH --datadir ~/ethereum-pow-blockchain/node1 init ~/ethereum-pow-blockchain/genesis.json
$GETH --datadir ~/ethereum-pow-blockchain/node2 init ~/ethereum-pow-blockchain/genesis.json
```

Both must print:
```
Successfully wrote genesis state    database=chaindata    hash=XXXXXX..XXXXXX
```

Both must show the **same hash** — this confirms they share the same genesis block.

---

## 5. genesis.json — Rules and Structure

```json
{
  "config": {
    "chainId": 12345,           ← your unique chain ID (avoid 1/56/137 — those are mainnets)
    "homesteadBlock": 0,        ← enable all EVM upgrades from block 0
    "eip150Block": 0,
    "eip155Block": 0,
    "eip158Block": 0,
    "byzantiumBlock": 0,
    "constantinopleBlock": 0,
    "petersburgBlock": 0,
    "istanbulBlock": 0,
    "berlinBlock": 0,
    "londonBlock": 0,
    "ethash": {}                ← ✅ REQUIRED — tells Geth to use Ethash PoW
  },
  "difficulty": "0x400",        ← low difficulty so mining starts fast locally
  "gasLimit": "0x8000000",      ← 134 million gas per block
  "extraData": "0x000...000",   ← exactly 32 zero bytes (required format)
  "alloc": {
    "ADDRESS_WITHOUT_0x": {     ← pre-fund your miner account
      "balance": "1000000000000000000000000"   ← in Wei (= 1,000,000 ETH)
    }
  }
}
```

### What NOT to include in genesis.json

| Field | Why to exclude |
|-------|---------------|
| `"terminalTotalDifficulty": 0` | Triggers the Merge immediately — chain becomes PoS, mining stops |
| `"terminalTotalDifficulty": any_value` | Same problem unless set astronomically high |
| `"mergeNetsplitBlock"` | Merge-related, avoid entirely |
| `"shanghaiTime"` | Post-merge upgrade, not compatible with v1.10.26 |

### Rules for alloc addresses

```json
✅ CORRECT — no 0x, address in quotes:
"alloc": {
    "80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2": {
        "balance": "1000000000000000000000000"
    }
}

❌ WRONG — 0x prefix not allowed here:
"alloc": {
    "0x80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2": { ... }
}

❌ WRONG — must be a string (quotes required):
"alloc": {
    0x80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2: { ... }
}
```

### Reinitializing after genesis changes

```bash
# Delete chain database only — NEVER delete keystore
rm -rf ~/ethereum-pow-blockchain/node1/geth
rm -rf ~/ethereum-pow-blockchain/node2/geth

# Re-init both
GETH=~/go-ethereum-pow/build/bin/geth
$GETH --datadir ~/ethereum-pow-blockchain/node1 init ~/ethereum-pow-blockchain/genesis.json
$GETH --datadir ~/ethereum-pow-blockchain/node2 init ~/ethereum-pow-blockchain/genesis.json
```

---

## 6. Starting the Nodes

Both nodes run in the background using `nohup`. Logs go to files you can check anytime.

### Kill everything and free all ports (run this before starting)

```bash
sudo pkill -f geth
sleep 2
sudo fuser -k 8545/tcp 2>/dev/null
sudo fuser -k 8546/tcp 2>/dev/null
sudo fuser -k 30303/tcp 2>/dev/null
sudo fuser -k 30304/tcp 2>/dev/null

# Verify all clear — should return nothing
sudo ss -tlnp | grep -E '8545|8546|30303|30304'
```

### Start node1 — Miner (background, logs to node1.log)

```bash
nohup ~/go-ethereum-pow/build/bin/geth \
  --datadir ~/ethereum-pow-blockchain/node1 \
  --networkid 12345 \
  --port 30303 \
  --http \
  --http.addr 0.0.0.0 \
  --http.port 8545 \
  --http.api admin,eth,miner,net,web3,personal \
  --allow-insecure-unlock \
  --mine \
  --miner.threads 1 \
  --miner.etherbase "0x80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2" \
  --unlock "0x80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2" \
  --password <(echo "p1@1234") \
  > ~/ethereum-pow-blockchain/node1.log 2>&1 &

echo "Node1 PID: $!"
```

### Start node2 — RPC (background, logs to node2.log)

> ⚠️ Note `--authrpc.port 8552` — this is required because node1 already uses the default auth port 8551.

```bash
nohup ~/go-ethereum-pow/build/bin/geth \
  --datadir ~/ethereum-pow-blockchain/node2 \
  --networkid 12345 \
  --port 30304 \
  --http \
  --http.addr 0.0.0.0 \
  --http.port 8546 \
  --http.api admin,eth,net,web3,personal \
  --authrpc.port 8552 \
  --bootnodes "enode://e0ca7d0dbe1b94b62d5d54d2f39c514812077713efed269fb6446d9269a1be1c21ceb8c3402046d89ec55eef79bd43a31c34114fa58f48401f775ca329bc9f13@127.0.0.1:30303" \
  > ~/ethereum-pow-blockchain/node2.log 2>&1 &

echo "Node2 PID: $!"
```

### Check logs anytime

```bash
tail -f ~/ethereum-pow-blockchain/node1.log
tail -f ~/ethereum-pow-blockchain/node2.log
# Press Ctrl+C to stop watching
```

---

## 7. Connecting the Nodes

The `--bootnodes` flag handles connection automatically at startup. If node2 still shows 0 peers after 30 seconds, add the peer manually via IPC:

```bash
# Attach to node2 IPC
~/go-ethereum-pow/build/bin/geth attach ~/ethereum-pow-blockchain/node2/geth.ipc

# Inside the console:
admin.addPeer("enode://e0ca7d0dbe1b94b62d5d54d2f39c514812077713efed269fb6446d9269a1be1c21ceb8c3402046d89ec55eef79bd43a31c34114fa58f48401f775ca329bc9f13@127.0.0.1:30303")

# Verify
admin.peers
# exit
exit
```

---

## 8. RPC Commands Reference

All commands below work as `curl` HTTP calls to either node. Node1 is on port `8545`, node2 on `8546`.

### Format

```bash
curl -s -X POST http://127.0.0.1:PORT \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"METHOD_NAME","params":[PARAMS],"id":1}'
```

---

### Block and Chain Info

#### Get current block number (hex)
```bash
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
# Result: {"result":"0x18"} → 0x18 = 24 in decimal
```

#### Get full block by number
```bash
# false = only tx hashes, true = full tx objects
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["0x1", false],"id":1}'
```

#### Get latest block
```bash
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_getBlockByNumber","params":["latest", false],"id":1}'
```

#### Get block by hash
```bash
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_getBlockByHash","params":["0xBLOCK_HASH", false],"id":1}'
```

#### Get chain ID
```bash
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_chainId","params":[],"id":1}'
# Result: {"result":"0x3039"} → 0x3039 = 12345
```

#### Get gas price
```bash
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_gasPrice","params":[],"id":1}'
```

#### Get transaction count in block (number of txs)
```bash
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_getBlockTransactionCountByNumber","params":["latest"],"id":1}'
```

---

### Account and Balance

#### Get balance of an address (returns Wei in hex)
```bash
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_getBalance","params":["0x80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2","latest"],"id":1}'
# Convert Wei to ETH: divide result by 10^18
```

#### Get transaction count (nonce) of an address
```bash
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_getTransactionCount","params":["0x80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2","latest"],"id":1}'
```

#### Get code at address (for smart contracts — returns 0x if not a contract)
```bash
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_getCode","params":["0xCONTRACT_ADDRESS","latest"],"id":1}'
```

---

### Mining and Network

#### Check if node is mining
```bash
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_mining","params":[],"id":1}'
# Result: {"result":true} or {"result":false}
```

#### Get miner hashrate
```bash
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_hashrate","params":[],"id":1}'
# Result in hashes/sec (hex)
```

#### Get coinbase (miner address)
```bash
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_coinbase","params":[],"id":1}'
```

#### Get peer count
```bash
curl -s -X POST http://127.0.0.1:8546 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"net_peerCount","params":[],"id":1}'
# Result: {"result":"0x1"} = 1 peer connected
```

#### Check if node is listening
```bash
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"net_listening","params":[],"id":1}'
```

#### Get network ID
```bash
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"net_version","params":[],"id":1}'
# Result: {"result":"12345"}
```

#### Check sync status
```bash
curl -s -X POST http://127.0.0.1:8546 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_syncing","params":[],"id":1}'
# false = fully synced
# {startingBlock, currentBlock, highestBlock} = syncing in progress
```

#### Get Geth client version
```bash
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"web3_clientVersion","params":[],"id":1}'
```

---

### Transactions

#### Send raw signed transaction
```bash
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_sendRawTransaction","params":["0xSIGNED_TX_HEX"],"id":1}'
```

#### Get transaction by hash
```bash
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_getTransactionByHash","params":["0xTX_HASH"],"id":1}'
```

#### Get transaction receipt (confirms if tx was mined)
```bash
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_getTransactionReceipt","params":["0xTX_HASH"],"id":1}'
# null = not mined yet
# object with blockNumber = confirmed
```

#### Estimate gas for a transaction
```bash
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{
    "jsonrpc":"2.0",
    "method":"eth_estimateGas",
    "params":[{
      "from": "0x80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2",
      "to": "0x7cc201Dcd87Dbbe7762b8Db914367D27478202e0",
      "value": "0xDE0B6B3A7640000"
    }],
    "id":1
  }'
```

#### Call a contract read function (no gas, no tx)
```bash
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{
    "jsonrpc":"2.0",
    "method":"eth_call",
    "params":[{
      "to": "0xCONTRACT_ADDRESS",
      "data": "0xFUNCTION_SELECTOR"
    }, "latest"],
    "id":1
  }'
```

---

### Logs and Events

#### Get logs (events) from a contract
```bash
curl -s -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  --data '{
    "jsonrpc":"2.0",
    "method":"eth_getLogs",
    "params":[{
      "fromBlock": "0x0",
      "toBlock": "latest",
      "address": "0xCONTRACT_ADDRESS"
    }],
    "id":1
  }'
```

---

### IPC Console Commands (attach to node directly)

```bash
# Attach to node1
~/go-ethereum-pow/build/bin/geth attach ~/ethereum-pow-blockchain/node1/geth.ipc

# Attach to node2
~/go-ethereum-pow/build/bin/geth attach ~/ethereum-pow-blockchain/node2/geth.ipc
```

Once inside the console:

```javascript
eth.blockNumber                          // current block
eth.mining                               // is node mining?
eth.hashrate                             // mining speed
eth.coinbase                             // miner address
eth.getBalance("0xADDRESS")             // balance in Wei
web3.fromWei(eth.getBalance("0xADDRESS"), "ether")   // balance in ETH
eth.getBlock("latest")                   // latest block details
eth.getBlock(5)                          // block number 5
eth.getTransaction("0xTX_HASH")          // tx details
eth.getTransactionReceipt("0xTX_HASH")  // tx receipt
net.peerCount                            // number of connected peers
admin.peers                              // detailed peer info
admin.nodeInfo                           // this node's enode and info
admin.nodeInfo.enode                     // just the enode string
miner.start(1)                           // start mining (1 thread)
miner.stop()                             // stop mining
miner.setEtherbase("0xADDRESS")         // set mining reward address
personal.listAccounts                    // list all accounts
personal.unlockAccount("0xADDR","pass",0)  // unlock account forever
```

---

## 9. Monitoring Commands

### Live dashboard (refreshes every 5 seconds)

```bash
watch -n 5 '
echo "=== $(date) ===" &&
echo -n "Node1 block : " && curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" --data "{\"jsonrpc\":\"2.0\",\"method\":\"eth_blockNumber\",\"params\":[],\"id\":1}" | grep -o "0x[^\"]*" &&
echo -n "Node1 mining: " && curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" --data "{\"jsonrpc\":\"2.0\",\"method\":\"eth_mining\",\"params\":[],\"id\":1}" | grep -o "true\|false" &&
echo -n "Node2 block : " && curl -s -X POST http://127.0.0.1:8546 -H "Content-Type: application/json" --data "{\"jsonrpc\":\"2.0\",\"method\":\"eth_blockNumber\",\"params\":[],\"id\":1}" | grep -o "0x[^\"]*" &&
echo -n "Node2 peers : " && curl -s -X POST http://127.0.0.1:8546 -H "Content-Type: application/json" --data "{\"jsonrpc\":\"2.0\",\"method\":\"net_peerCount\",\"params\":[],\"id\":1}" | grep -o "0x[^\"]*" &&
echo -n "Miner balance (Wei): " && curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" --data "{\"jsonrpc\":\"2.0\",\"method\":\"eth_getBalance\",\"params\":[\"0x80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2\",\"latest\"],\"id\":1}" | grep -o "0x[^\"]*"
'
```

Press `Ctrl+C` to stop.

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

### Watch node logs live

```bash
tail -f ~/ethereum-pow-blockchain/node1.log   # miner logs
tail -f ~/ethereum-pow-blockchain/node2.log   # rpc logs
# Ctrl+C to stop
```

### Check geth processes are running

```bash
ps aux | grep geth | grep -v grep
```

---

## 10. Common Errors and Fixes

### Error: `No such file or directory` for geth binary

Repo was cloned with a different name. Correct path is:
```bash
~/go-ethereum-pow/build/bin/geth
```

### Error: Bootstrap URL invalid / missing 'enr:' prefix

You used the placeholder text instead of the real enode:
```bash
# Wrong
--bootnodes "ENODE_FROM_NODE1_WITH_127.0.0.1"

# Correct — paste the actual enode string
--bootnodes "enode://e0ca7d...@127.0.0.1:30303"
```

### Error: `listen tcp 127.0.0.1:8551: bind: address already in use`

Both nodes try to use auth port 8551 by default. Node2 must use a different one.
Add `--authrpc.port 8552` to the node2 start command:
```bash
# Add this flag to node2 only
--authrpc.port 8552
```

### Error: `HTTP server graceful shutdown timed out` on node2

This happens because port 8546 or 8551 was occupied by a previous crashed instance. Fix:
```bash
sudo fuser -k 8546/tcp 2>/dev/null
sudo fuser -k 30304/tcp 2>/dev/null
# Then restart node2
```

### Error: `Consensus: Beacon` instead of `Consensus: Ethash`

`terminalTotalDifficulty` is in your genesis.json. Remove it, delete both geth databases, and reinitialize.

### Error: `eth.blockNumber` stuck at 0

DAG is still generating. Check node1 logs:
```bash
grep "Generating DAG" ~/ethereum-pow-blockchain/node1.log | tail -5
```
Wait until `percentage=100` — then mining begins automatically. Takes 2-3 minutes.

### Error: `Successfully wrote genesis state` but different hashes

genesis.json was changed between initializing node1 and node2. Delete both geth directories and re-init both using the exact same genesis.json file.

### Error: `externally-managed-environment` on pip install

```bash
# Use a virtual environment
python3 -m venv ~/eth-venv
~/eth-venv/bin/pip install eth-account
~/eth-venv/bin/python3 /tmp/your_script.py
```

### Error: `EOF when reading a line` in Python script

Don't use heredoc (`<< 'EOF'`) for interactive scripts that use `input()`. Save to a file first:
```bash
cat > /tmp/script.py << 'PYEOF'
# your script here
PYEOF
~/eth-venv/bin/python3 /tmp/script.py
```

### Chain accidentally started as mainnet

```bash
rm -rf ~/.ethereum
rm -rf ~/.ethash
# Always use --datadir when starting geth
```

### Node2 shows 0 peers after startup

The bootnodes flag may not have connected automatically. Manually add the peer:
```bash
~/go-ethereum-pow/build/bin/geth attach ~/ethereum-pow-blockchain/node2/geth.ipc
# Inside console:
admin.addPeer("enode://e0ca7d0dbe1b94b62d5d54d2f39c514812077713efed269fb6446d9269a1be1c21ceb8c3402046d89ec55eef79bd43a31c34114fa58f48401f775ca329bc9f13@127.0.0.1:30303")
```

---

## 11. Port Reference

| Node | Role | P2P Port | RPC Port | Auth RPC Port |
|------|------|----------|----------|---------------|
| node1 | Miner | 30303 | 8545 | 8551 (default) |
| node2 | RPC | 30304 | 8546 | 8552 (custom) |

---

## 12. Useful References

| Resource | URL |
|----------|-----|
| Geth v1.10.26 release | https://github.com/ethereum/go-ethereum/releases/tag/v1.10.26 |
| Go 1.21.13 download | https://go.dev/dl/go1.21.13.linux-amd64.tar.gz |
| Geth JSON-RPC API | https://geth.ethereum.org/docs/interacting-with-geth/rpc |
| Geth management API | https://geth.ethereum.org/docs/interacting-with-geth/rpc/ns-personal |
| JSON-RPC spec | https://ethereum.org/en/developers/docs/apis/json-rpc |

---

## Quick Start (nodes already built and initialized)

```bash
# Kill any existing geth
sudo pkill -f geth && sleep 2

# Start node1 (miner)
nohup ~/go-ethereum-pow/build/bin/geth \
  --datadir ~/ethereum-pow-blockchain/node1 \
  --networkid 12345 --port 30303 \
  --http --http.addr 0.0.0.0 --http.port 8545 \
  --http.api admin,eth,miner,net,web3,personal \
  --allow-insecure-unlock --mine --miner.threads 1 \
  --miner.etherbase "0x80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2" \
  --unlock "0x80a63d2C5cB3D83E3ea235C98Cd64710C43e1EF2" \
  --password <(echo "p1@1234") \
  > ~/ethereum-pow-blockchain/node1.log 2>&1 &

sleep 3

# Start node2 (RPC)
nohup ~/go-ethereum-pow/build/bin/geth \
  --datadir ~/ethereum-pow-blockchain/node2 \
  --networkid 12345 --port 30304 \
  --http --http.addr 0.0.0.0 --http.port 8546 \
  --http.api admin,eth,net,web3,personal \
  --authrpc.port 8552 \
  --bootnodes "enode://e0ca7d0dbe1b94b62d5d54d2f39c514812077713efed269fb6446d9269a1be1c21ceb8c3402046d89ec55eef79bd43a31c34114fa58f48401f775ca329bc9f13@127.0.0.1:30303" \
  > ~/ethereum-pow-blockchain/node2.log 2>&1 &

sleep 5

# Verify both running
echo "Node1 mining:" && curl -s -X POST http://127.0.0.1:8545 -H "Content-Type: application/json" --data '{"jsonrpc":"2.0","method":"eth_mining","params":[],"id":1}'
echo ""
echo "Node2 peers:" && curl -s -X POST http://127.0.0.1:8546 -H "Content-Type: application/json" --data '{"jsonrpc":"2.0","method":"net_peerCount","params":[],"id":1}'
```
