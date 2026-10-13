Public address of the miner_node_aws key:   0xDA6d26deC4E58cF029402613c3e5401Cb03A1357

On-prem setup: see quick_start.md and ops/onprem/config.example.json.
The identities below were supplied for the existing AWS deployment. Their
loopback addresses are usable only on that AWS host. Remote connections need
reachable AWS public/VPN IPs and inbound TCP/UDP 30303 (RPC), 30304 (miner).

Both AWS nodes run on 16.60.82.161 (confirmed by the user).
AWS HTTPS RPC at that IP reports chain/network ID 5356 and genesis hash
0xdd1301fd0ca034e5f60c87919d01933dcc563333f6064f24d6a256b5f03f9bc8.
The user confirmed AWS uses this repository's genesis.json, and its hash matches.
TCP 30303 and 30304 are reachable from on-prem after the AWS rules were added.
HTTPS 443 is also reachable.
Current on-prem public egress IP: 149.40.242.241. Allow TCP and UDP
30303-30304 on AWS from 149.40.242.241/32 (recheck if egress changes).
Both on-prem services and the daily log rotation timer are active and enabled.
On-prem mining rewards go to 0x9aA69b409dA18d8c2A6D49a3C31a71EE84068E79,
configured in onprem-config.json. No wallet private key is needed for mining.
Both local nodes are synchronized with AWS, each with three peers: both AWS
nodes and its local partner. On-prem block 30785 was verified on both local
nodes and AWS, rewarding the configured wallet. RPC binds to 127.0.0.1:8545.

Local directories: miner_node_onprem/, rpc_node_onprem/, logs/.
Service logs: logs/geth-miner.log and logs/geth-rpc.log.
The installer enables daily rotation with seven compressed archives.


aws miner enode
"enode://cc2a54c1c5d7f4c4f64cb4143f686d050f92a326bea33303317002309ad458dcbf9aed2f964ad0830a2e392a212db2f08a70f3264f5e0125c9ac5071f68cc967@127.0.0.1:30304"


aws rpc enode
"enode://541cb0e3f8d812f2903dc8775ca1b0a193ca58f87e2675477a450981dde38791a651cc99830604b7cba4ad7b8d190691ba23eebabc075a8eae492a3fc292b495@127.0.0.1:30303"

on-prem rpc enode (local address)
"enode://de150c4a33dfd8dd3b56027dd8aec1891fe8437f752af5434b9ec661ec5708cfad6416aea3b77fa6c0f3a0023ab78fa53829a2062c7c0f6472142a2f22f55e30@127.0.0.1:30303"

on-prem miner enode (local address)
"enode://4b76df19b1f01a5e6d8730b26a9ee9d8ed378a2b27d226d3b931b9bb9975306c29d006a7d009ad9d0e33c17478635e50f18f0c24b8451e5ad0512cca322ca367@127.0.0.1:30304"

For inbound AWS connections, replace 127.0.0.1 with a verified reachable
on-prem/VPN IP and allow/forward TCP+UDP 30303/30304. These loopback URLs work
only on this machine; current AWS connections are initiated outbound.



