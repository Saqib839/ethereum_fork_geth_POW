# Ethereum PoW: AWS + on-prem

AWS miner and RPC: **16.60.82.161**. Add one miner and one RPC locally using Geth **1.10.26**, chain/network ID **5356**, and this repository's genesis.

- [Quick setup](quick_start.md): ports, configuration, services, sync.
- [Log rotation](log_rotation_guide.md): daily rotation, seven compressed archives.
- [HTTPS RPC](nginx_rpc_setup.md): optional wallet access.

One surviving miner can produce blocks. RPC access requires a reachable endpoint and client/proxy failover. An RPC-only survivor cannot produce blocks; network partitions can cause reorganizations.
