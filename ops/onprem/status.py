#!/usr/bin/env python3
"""Read local IPC state and optionally compare with a reachable AWS RPC URL."""
import json
import os
import pwd
from pathlib import Path
import subprocess
import sys
import urllib.request

EXPR = '''JSON.stringify({genesis:eth.getBlock(0).hash,chain:eth.chainId(),
network:net.version,height:eth.blockNumber,syncing:eth.syncing,mining:eth.mining,
peers:admin.peers.map(function(p){return {id:p.id,enode:p.enode,address:p.network.remoteAddress}}),
latest:eth.getBlock("latest").hash})'''


def remote(url, method, params):
    req = urllib.request.Request(url, json.dumps({
        'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode(),
        {'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=15) as response:
        data = json.load(response)
    if 'error' in data or 'result' not in data:
        raise ValueError(data)
    return data['result']


def ipc(expected, role, expression):
    args = ['/usr/local/lib/ethereum-pow/geth', 'attach', '--exec', expression,
            str(Path(expected['datadirs'][role]) / 'geth.ipc')]
    if os.getuid() != pwd.getpwnam(expected['service_user']).pw_uid:
        args = ['runuser', '-u', expected['service_user'], '--', *args]
    result = subprocess.run(args,
        check=True, text=True, capture_output=True, timeout=20)
    return json.loads(json.loads(result.stdout.strip()))


def main():
    if len(sys.argv) > 2:
        sys.exit('Usage: sudo python3 ops/onprem/status.py [AWS_RPC_URL]')
    states = {}
    failed = False
    try:
        expected = json.loads(Path('/etc/ethereum-pow/network.json').read_text())
    except (OSError, ValueError) as error:
        sys.exit(f'Run the installer first; cannot read installed network identity: {error}')
    for role in ('rpc', 'miner'):
        try:
            states[role] = ipc(expected, role, EXPR)
            print(role + ': ' + json.dumps(states[role], indent=2))
            if not states[role]['peers'] or states[role]['syncing'] is not False:
                failed = True
            if states[role]['chain'] != '0x14ec' or states[role]['network'] != '5356':
                failed = True
            if role == 'miner' and states[role]['mining'] is not True:
                failed = True
            if expected:
                if states[role]['genesis'] != expected['genesis_hash']:
                    print(f'{role}: genesis differs from configured AWS genesis', file=sys.stderr)
                    failed = True
                connected = {p['enode'].split('@')[0].lower()
                             for p in states[role]['peers'] if p.get('enode')}
                aws_connected = [peer for peer in expected['aws_enodes']
                                 if peer.split('@')[0].lower() in connected]
                print(f'{role}: direct AWS connections={len(aws_connected)}/2')
                if not aws_connected:
                    print(f'{role}: no direct AWS peer; local peers alone do not prove AWS sync',
                          file=sys.stderr)
                    failed = True
                elif len(aws_connected) < 2:
                    print(f'{role}: one AWS peer is unavailable; inspect its port/service')
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            print(f'{role}: {error}', file=sys.stderr)
            failed = True
    if len(states) == 2 and states['rpc']['genesis'] != states['miner']['genesis']:
        print('ERROR: local genesis mismatch', file=sys.stderr)
        failed = True
    if len(states) == 2 and states['rpc']['height'] == states['miner']['height']:
        if states['rpc']['latest'] != states['miner']['latest']:
            print('ERROR: local nodes disagree at the same block height', file=sys.stderr)
            failed = True
    if len(sys.argv) == 2:
        try:
            genesis = remote(sys.argv[1], 'eth_getBlockByNumber', ['0x0', False])['hash']
            height = int(remote(sys.argv[1], 'eth_blockNumber', []), 16)
            print(f'AWS: genesis={genesis}, height={height}')
            for role, state in states.items():
                common = min(height, state['height'])
                aws_hash = remote(sys.argv[1], 'eth_getBlockByNumber', [hex(common), False])['hash']
                matches = ipc(expected, role, f'JSON.stringify(eth.getBlock({common}).hash)') == aws_hash
                print(f'{role}: AWS height lag={height-state["height"]}, '
                      f'same block at height {common}={matches}')
                if genesis != state['genesis'] or not matches or abs(height-state['height']) > 2:
                    failed = True
        except Exception as error:
            print(f'AWS comparison failed: {error}', file=sys.stderr)
            failed = True
    print('Repeat after 30 seconds: heights must advance; inspect AWS peer IDs above.')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
