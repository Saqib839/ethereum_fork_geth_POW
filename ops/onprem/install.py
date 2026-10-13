#!/usr/bin/env python3
"""Install two persistent Geth services after verifying the AWS genesis."""
import ipaddress
import json
import os
import pwd
import grp
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CONF = Path('/etc/ethereum-pow')
GETH = Path('/usr/local/lib/ethereum-pow/geth')
USER = 'ethereum-pow'


def run(args, **kwargs):
    return subprocess.run([str(a) for a in args], check=True, text=True, **kwargs)


def probe(binary, datadir, expression, as_user=False):
    args = [binary, '--datadir', datadir, '--networkid', '5356',
            '--syncmode', 'full', '--nodiscover', '--maxpeers', '0',
            '--port', '0', '--authrpc.addr', '127.0.0.1', '--authrpc.port', '0',
            '--ethash.dagdir', str(Path(datadir) / 'ethash'),
            '--ethash.cachedir', str(Path(datadir) / 'ethash-cache'),
            '--nat', 'none', '--ipcdisable', '--exec', expression, 'console']
    if as_user:
        args = ['runuser', '-u', USER, '--', *args]
    result = run(args, capture_output=True, timeout=60)
    lines = result.stdout.strip().splitlines()
    return json.loads(json.loads(lines[-1]))


def write(path, content):
    temp = path.with_suffix(path.suffix + '.new')
    temp.write_text(content)
    temp.chmod(0o644)
    temp.replace(path)


def unit_quote(value):
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%') + '"'


def rotation_config(logs, user, group):
    return f'''"{logs}/*.log" {{
    su {user} {group}
    daily
    rotate 7
    compress
    missingok
    notifempty
    copytruncate
}}
'''


def main():
    global USER
    if len(sys.argv) not in (2, 3) or (len(sys.argv) == 3 and sys.argv[2] != '--start'):
        sys.exit('Usage: sudo python3 ops/onprem/install.py config.json [--start]')
    if os.geteuid() != 0:
        sys.exit('Run with sudo; this installs systemd services.')
    config_path = Path(sys.argv[1]).resolve()
    cfg = json.loads(config_path.read_text())
    base = Path(cfg.get('data_directory', '.'))
    if not base.is_absolute():
        base = (config_path.parent / base).resolve()
    USER = cfg.get('service_user') or pwd.getpwuid(config_path.parent.stat().st_uid).pw_name
    account = pwd.getpwnam(USER)
    if account.pw_uid == 0:
        sys.exit('Set service_user to an existing non-root Linux user.')
    group = grp.getgrgid(account.pw_gid).gr_name
    directories = {role: base / f'{role}_node_onprem' for role in ('rpc', 'miner')}
    logs = base / 'logs'
    if not shutil.which('logrotate'):
        sys.exit('Install logrotate first: sudo apt install logrotate')
    for key in ('aws_miner_host', 'aws_rpc_host'):
        ip = ipaddress.ip_address(cfg[key])
        if ip.version != 4 or ip.is_loopback or ip.is_unspecified or ip.is_multicast:
            sys.exit(f'{key}: use a reachable public or VPN IPv4 address.')
    for key in ('aws_miner_port', 'aws_rpc_port'):
        if type(cfg[key]) is not int or not 1 <= cfg[key] <= 65535:
            sys.exit(f'Invalid {key}')
    for key in ('aws_miner_id', 'aws_rpc_id'):
        if not re.fullmatch(r'[0-9a-fA-F]{128}', cfg[key]):
            sys.exit(f'Invalid {key}')
    expected = cfg['aws_genesis_hash'].lower()
    if not re.fullmatch(r'0x[0-9a-f]{64}', expected):
        sys.exit('Copy aws_genesis_hash from the running AWS node first.')
    reward = cfg['miner_reward_address']
    if not re.fullmatch(r'0x[0-9a-fA-F]{40}', reward) or int(reward, 16) == 0:
        sys.exit('Set miner_reward_address to your public wallet address.')
    threads = cfg.get('miner_threads', 1)
    if type(threads) is not int or threads < 1:
        sys.exit('miner_threads must be a positive integer.')
    advertise = cfg.get('advertise_ip', '')
    if advertise:
        ip = ipaddress.ip_address(advertise)
        if ip.version != 4 or ip.is_loopback or ip.is_unspecified or ip.is_multicast:
            sys.exit('advertise_ip must be a reachable public or VPN IPv4 address.')
    genesis = Path(cfg['genesis_file'])
    if not genesis.is_absolute():
        genesis = (config_path.parent / genesis).resolve()
    data = json.loads(genesis.read_text())
    if data['config']['chainId'] != 5356 or 'ethash' not in data['config']:
        sys.exit('Expected AWS Ethash chain ID 5356.')
    arch = os.uname().machine
    names = {'x86_64': 'amd64', 'aarch64': 'arm64'}
    if arch not in names:
        sys.exit(f'Unsupported architecture: {arch}')
    binary = ROOT / 'bin' / f'geth-linux-{names[arch]}'
    version = run([binary, 'version'], capture_output=True).stdout
    if 'Version: 1.10.26-stable' not in version:
        sys.exit('Expected bundled Geth 1.10.26-stable.')
    for role in ('rpc', 'miner'):
        state = subprocess.run(['systemctl', 'is-active', f'ethereum-pow-{role}'],
                               capture_output=True, text=True).stdout.strip()
        if state in ('active', 'activating', 'deactivating', 'reloading'):
            sys.exit('Stop both ethereum-pow services before rerunning the installer.')
    # Detect another application using these ports before installing anything.
    for port in (30303, 30304, 8545, 8551, 8552):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            try:
                listener.bind(('0.0.0.0', port))
            except OSError as error:
                sys.exit(f'TCP port {port} is unavailable: {error}')
        if port in (30303, 30304):
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as listener:
                try:
                    listener.bind(('0.0.0.0', port))
                except OSError as error:
                    sys.exit(f'UDP port {port} is unavailable: {error}')
    # Verify in an isolated temporary database before touching persistent data.
    with tempfile.TemporaryDirectory(prefix='ethereum-genesis-') as temp:
        run([binary, '--datadir', temp, 'init', genesis], capture_output=True)
        actual = probe(binary, temp, 'JSON.stringify(eth.getBlock(0).hash)')
        if actual.lower() != expected:
            sys.exit(f'Genesis mismatch: file={actual}, AWS={expected}. Use the AWS genesis file.')
    CONF.mkdir(parents=True, exist_ok=True)
    GETH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(binary, GETH)
    GETH.chmod(0o755)
    # Install a snapshot of the verified genesis; never wipe databases or node keys.
    write(CONF / 'genesis.json', json.dumps(data, indent=2) + '\n')
    ids = {}
    for role in ('rpc', 'miner'):
        directory = directories[role]
        directory.mkdir(parents=True, exist_ok=True)
        run(['chown', f'{USER}:{group}', directory])
        directory.chmod(0o700)
        run(['runuser', '-u', USER, '--', GETH, '--datadir', directory,
             'init', CONF / 'genesis.json'])
        info = probe(GETH, directory,
                     'JSON.stringify({id:admin.nodeInfo.enode.split("@")[0].slice(8),hash:eth.getBlock(0).hash})', True)
        if info['hash'].lower() != expected:
            sys.exit(f'{role} existing database does not match AWS; preserve it and investigate.')
        ids[role] = info['id']
    logs.mkdir(parents=True, exist_ok=True)
    run(['chown', f'{USER}:{group}', logs])
    logs.chmod(0o750)
    for role in ('rpc', 'miner'):
        logfile = logs / f'geth-{role}.log'
        logfile.touch(exist_ok=True)
        run(['chown', f'{USER}:{group}', logfile])
        logfile.chmod(0o640)
    rotation = Path('/etc/logrotate.d/ethereum-pow-onprem')
    write(rotation, rotation_config(logs, USER, group))
    # Use a dedicated timer and state file to avoid relying on distro scheduling.
    # Global logrotate may also include this rule; both schedulers use the same
    # state file and its lock, so they do not rotate it twice on the same day.
    logrotate = shutil.which('logrotate')
    write(Path('/etc/systemd/system/ethereum-pow-logrotate.service'), f'''[Unit]
Description=Rotate on-prem Ethereum logs

[Service]
Type=oneshot
ExecStart={unit_quote(logrotate)} --state /var/lib/logrotate/status {unit_quote(rotation)}
''')
    write(Path('/etc/systemd/system/ethereum-pow-logrotate.timer'), '''[Unit]
Description=Daily rotation of on-prem Ethereum logs

[Timer]
OnCalendar=daily
Persistent=true
RandomizedDelaySec=5m

[Install]
WantedBy=timers.target
''')
    aws = [f"enode://{cfg[f'aws_{role}_id']}@{cfg[f'aws_{role}_host']}:{cfg[f'aws_{role}_port']}"
           for role in ('miner', 'rpc')]
    write(CONF / 'network.json', json.dumps({
        'genesis_hash': expected,
        'aws_enodes': aws,
        'service_user': USER,
        'datadirs': {role: str(directory) for role, directory in directories.items()},
    }, indent=2) + '\n')
    for role, port, other, other_port, auth in (
        ('rpc', 30303, 'miner', 30304, 8552), ('miner', 30304, 'rpc', 30303, 8551)):
        peers = [*aws, f'enode://{ids[other]}@127.0.0.1:{other_port}']
        write(CONF / f'{role}.toml', '[Node.P2P]\n' +
              f'StaticNodes = {json.dumps(peers)}\nBootstrapNodes = {json.dumps(aws)}\n')
        args = [str(GETH), '--config', str(CONF / f'{role}.toml'),
                '--datadir', str(directories[role]), '--networkid', '5356', '--syncmode', 'full',
                '--port', str(port), '--maxpeers', '25', '--nat',
                f'extip:{advertise}' if advertise else 'none',
                '--ethash.dagdir', str(directories[role] / 'ethash'),
                '--ethash.cachedir', str(directories[role] / 'ethash-cache'),
                '--authrpc.addr', '127.0.0.1', '--authrpc.port', str(auth)]
        if role == 'miner':
            args += ['--mine', '--miner.etherbase', reward, '--miner.threads', str(threads)]
        else:
            args += ['--http', '--http.addr', '127.0.0.1', '--http.port', '8545',
                     '--http.api', 'eth,net,web3', '--http.vhosts', 'localhost,127.0.0.1']
        unit = f'''[Unit]
Description=Ethereum PoW on-prem {role}
Wants=network-online.target
After=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
User={USER}
Group={group}
ExecStart={' '.join(unit_quote(arg) for arg in args)}
Restart=always
RestartSec=10
TimeoutStopSec=180
KillSignal=SIGINT
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=read-only
ProtectSystem=strict
ReadWritePaths={unit_quote(directories[role])} {unit_quote(logs)}
StandardOutput=append:{logs / f'geth-{role}.log'}
StandardError=append:{logs / f'geth-{role}.log'}

[Install]
WantedBy=multi-user.target
'''
        write(Path('/etc/systemd/system') / f'ethereum-pow-{role}.service', unit)
    write(CONF / 'enodes.json', json.dumps({
        role: f"enode://{ids[role]}@{advertise or 'REPLACE_WITH_ONPREM_REACHABLE_IP'}:{port}"
        for role, port in (('rpc', 30303), ('miner', 30304))}, indent=2) + '\n')
    run(['systemctl', 'daemon-reload'])
    run(['systemctl', 'enable', '--now', 'ethereum-pow-logrotate.timer'])
    if '--start' in sys.argv:
        run(['systemctl', 'enable', '--now', 'ethereum-pow-rpc', 'ethereum-pow-miner'])
    print('Installed. Enodes: /etc/ethereum-pow/enodes.json')
    print('Start: sudo systemctl enable --now ethereum-pow-rpc ethereum-pow-miner')


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as error:
        sys.exit(f'{error}\n{error.stdout or ""}\n{error.stderr or ""}')
    except (KeyError, ValueError, OSError, subprocess.SubprocessError) as error:
        sys.exit(str(error))
