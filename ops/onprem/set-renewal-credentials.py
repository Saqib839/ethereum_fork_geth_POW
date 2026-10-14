#!/usr/bin/env python3
"""Accept dedicated renewal credentials interactively, never through chat or argv."""
import configparser
import getpass
import os
from pathlib import Path
import tempfile

if os.geteuid() != 0:
    raise SystemExit('Run with sudo in your SSH terminal.')
root = Path('/root/.aws')
root.mkdir(mode=0o700, exist_ok=True)
path = root / 'credentials'
config = configparser.ConfigParser()
if path.exists():
    config.read(path)
    if config.has_section('default'):
        raise SystemExit('Existing default credentials found; inspect before replacing.')
key = getpass.getpass('AWS access key ID (hidden): ').strip()
secret = getpass.getpass('AWS secret access key (hidden): ').strip()
if not key or not secret:
    raise SystemExit('Both values are required; nothing saved.')
config['default'] = {'aws_access_key_id': key, 'aws_secret_access_key': secret}
fd, temporary = tempfile.mkstemp(dir=root, prefix='credentials-')
with os.fdopen(fd, 'w') as output:
    config.write(output)
os.replace(temporary, path)
print('Saved root-only credentials. Values were not printed.')
