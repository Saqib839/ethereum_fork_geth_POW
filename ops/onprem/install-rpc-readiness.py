#!/usr/bin/env python3
"""Install the host-header fix and dynamic health check without touching datadirs."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
SITE = Path('/etc/nginx/sites-available/rpc.markettrackerx.com')
LOCATION = '''    location = /healthz {
        proxy_pass http://127.0.0.1:18545/healthz;
        proxy_set_header Host localhost;
        proxy_connect_timeout 1s;
        proxy_read_timeout 4s;
        proxy_intercept_errors on;
        error_page 500 502 504 =503 @rpc_unready;
        add_header Cache-Control "no-store" always;
    }
    location @rpc_unready {
        default_type text/plain;
        return 503 "rpc-not-ready";
    }

'''


def run(*args):
    subprocess.run(args, check=True)


def main():
    if os.geteuid() != 0:
        sys.exit('Run this installer with sudo.')
    # Refuse changes if the expected local chain is not ready.
    run('/usr/bin/python3', str(HERE / 'rpc_health.py'), '--check')
    original = SITE.read_text()
    updated = original.replace('proxy_set_header Host $host;', 'proxy_set_header Host localhost;')
    if 'location = /healthz' not in updated:
        marker = '    location / {'
        if updated.count(marker) != 2:
            sys.exit('Unexpected Nginx layout; inspect before editing.')
        # Both HTTP and HTTPS health checks must return their actual readiness.
        updated = updated.replace(marker, LOCATION + marker)
    if 'proxy_set_header Host localhost;' not in updated:
        sys.exit('Cannot locate upstream Host directive.')
    backup = Path('/var/backups/ethereum-rpc')
    backup.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SITE, backup / ('nginx-' + str(time.time_ns()) + '.conf'))
    destination = Path('/usr/local/lib/ethereum-pow')
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HERE / 'rpc_health.py', destination / 'rpc_health.py')
    (destination / 'rpc_health.py').chmod(0o644)
    shutil.copyfile(HERE / 'ethereum-rpc-health.service',
                    '/etc/systemd/system/ethereum-rpc-health.service')
    run('systemctl', 'daemon-reload')
    run('systemctl', 'enable', '--now', 'ethereum-rpc-health.service')
    run('systemctl', 'restart', 'ethereum-rpc-health.service')
    try:
        SITE.write_text(updated)
        run('nginx', '-t')
        run('systemctl', 'reload', 'nginx')
    except Exception:
        SITE.write_text(original)
        run('nginx', '-t')
        run('systemctl', 'reload', 'nginx')
        raise
    print('Host header fixed; /healthz enabled over HTTP and HTTPS; datadirs untouched.')


if __name__ == '__main__':
    main()
