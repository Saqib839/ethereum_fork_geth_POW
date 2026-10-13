Public address of the miner_node_aws key:   0xDA6d26deC4E58cF029402613c3e5401Cb03A1357

On-prem setup: see quick_start.md and ops/onprem/config.example.json.
The identities below were supplied for the existing AWS deployment. Their
loopback addresses are usable only on that AWS host. Remote connections need
reachable AWS public/VPN IPs and inbound TCP/UDP 30303 (RPC), 30304 (miner).

Both AWS nodes run on 16.60.82.161 (confirmed by the user).
AWS HTTPS RPC at that IP reports chain/network ID 5356 and genesis hash
0xdd1301fd0ca034e5f60c87919d01933dcc563333f6064f24d6a256b5f03f9bc8.
The user confirmed AWS uses this repository's genesis.json, and its hash matches.
TCP 30303 and 30304 timed out from on-prem; HTTPS 443 was reachable.
Current on-prem public egress IP: 149.40.242.241. Allow TCP and UDP
30303-30304 on AWS from 149.40.242.241/32 (recheck if egress changes).
Pending deployment: AWS peer-port reachability and local sudo execution.
On-prem mining rewards go to 0x9aA69b409dA18d8c2A6D49a3C31a71EE84068E79,
configured in onprem-config.json. No wallet private key is needed for mining.
Live synchronization has not yet been established.

Local directories: miner_node_onprem/, rpc_node_onprem/, logs/.
Service logs: logs/geth-miner.log and logs/geth-rpc.log.
The installer enables daily rotation with seven compressed archives.


aws miner enode
"enode://cc2a54c1c5d7f4c4f64cb4143f686d050f92a326bea33303317002309ad458dcbf9aed2f964ad0830a2e392a212db2f08a70f3264f5e0125c9ac5071f68cc967@127.0.0.1:30304"


aws rpc enode
"enode://541cb0e3f8d812f2903dc8775ca1b0a193ca58f87e2675477a450981dde38791a651cc99830604b7cba4ad7b8d190691ba23eebabc075a8eae492a3fc292b495@127.0.0.1:30303"



