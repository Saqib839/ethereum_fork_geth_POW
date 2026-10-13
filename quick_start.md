# Quick setup

AWS miner + RPC already run on **16.60.82.161**. The example contains their enodes, verified genesis hash, and mining reward address. No wallet private key is needed.

## 1. Open AWS ports

In the VM's security group and firewall, allow **TCP + UDP 30303–30304** from **149.40.242.241/32** (current on-prem egress IP). Keep 8545/8551/8552 private. If ports still time out, check AWS Geth listeners with `sudo ss -lntup`.

## 2. Configure

`onprem-config.json` is already filled on this machine. On a fresh checkout:

```bash
cp ops/onprem/config.example.json onprem-config.json
```

Change `miner_reward_address` only if you want another reward wallet. `service_user` defaults to the config directory's owner; `data_directory` defaults to that directory. Preserve each node's `geth/nodekey`; these identity keys are generated automatically and are separate from wallet keys.

## 3. Install and start

```bash
sudo apt install -y logrotate
sudo python3 ops/onprem/install.py onprem-config.json --start
sudo systemctl status ethereum-pow-rpc ethereum-pow-miner --no-pager
```

The installer uses `rpc_node_onprem/`, `miner_node_onprem/`, and `logs/`. Services restart after a crash and start on boot. RPC listens on loopback 8545; P2P ports are 30303/30304. A daily timer rotates both logs automatically. The installer verifies genesis and preserves existing data; stop both local services before rerunning it.

## 4. Check synchronization

```bash
python3 ops/onprem/status.py
tail -n 30 logs/geth-rpc.log logs/geth-miner.log
```

Repeat after 30 seconds: heights should advance, `syncing` should become false, and both local nodes should connect directly to AWS. Compare shared block hashes when the AWS HTTPS URL is available:

```bash
python3 ops/onprem/status.py https://rpc.markettrackerx.com
```

Ensure that hostname resolves to your intended AWS VM. Initial sync and mining DAG generation take time. Local peers alone do not prove AWS sync.

## 5. AWS reconnection and failover

Both local nodes persistently dial both AWS peers. For inbound reconnection too, allow on-prem TCP/UDP 30303–30304 from AWS, forward those ports if behind NAT, and set `advertise_ip` to the reachable public/VPN IP.

Read `/etc/ethereum-pow/enodes.json`. Add both reachable local enodes to each AWS node's existing `[Node.P2P] StaticNodes` list, retaining its AWS partner. Ensure its service loads that TOML with `--config`. Apply AWS changes one node at a time after local sync; restart a miner only while another connected miner produces blocks.

Configure wallets/libraries with both HTTPS endpoints, or use the [proxy failover example](ops/onprem/rpc-failover.nginx.conf.example). Client retries are required for failed POSTs. One proxy is a failure point; passive failover does not detect stale HTTP 200 responses. See [HTTPS setup](nginx_rpc_setup.md).
