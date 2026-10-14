#!/usr/bin/env python3
"""Fail-closed readiness checks for the local Geth RPC; no AWS dependency."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import os
import time
import urllib.request

GENESIS = '0xdd1301fd0ca034e5f60c87919d01933dcc563333f6064f24d6a256b5f03f9bc8'
RPC_URL = 'http://127.0.0.1:8545'
MAX_AGE = int(os.environ.get('RPC_MAX_BLOCK_AGE', '300'))
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def batch(calls):
    payload = [{'jsonrpc': '2.0', 'id': i, 'method': method, 'params': params}
               for i, (method, params) in enumerate(calls)]
    request = urllib.request.Request(RPC_URL, json.dumps(payload).encode(),
                                     {'Content-Type': 'application/json', 'Host': 'localhost'})
    with OPENER.open(request, timeout=1.5) as response:
        replies = json.load(response)
    if not isinstance(replies, list) or len(replies) != len(calls):
        raise ValueError('incomplete RPC batch')
    results = {}
    for reply in replies:
        ident = reply.get('id')
        if (type(ident) is not int or ident not in range(len(calls)) or ident in results
                or reply.get('jsonrpc') != '2.0' or 'error' in reply
                or reply.get('result') is None):
            raise ValueError('RPC error or invalid response')
        results[ident] = reply['result']
    return [results[i] for i in range(len(calls))]


def check_ready():
    chain, genesis, syncing, latest = batch([
        ('eth_chainId', []), ('eth_getBlockByNumber', ['0x0', False]),
        ('eth_syncing', []), ('eth_getBlockByNumber', ['latest', False])])
    if chain != '0x14ec' or genesis['hash'].lower() != GENESIS:
        raise ValueError('chain identity mismatch')
    if syncing is not False:
        raise ValueError('node is syncing')
    age = time.time() - int(latest['timestamp'], 16)
    if int(latest['number'], 16) == 0 or age < -30 or age > MAX_AGE:
        raise ValueError('latest block is stale or has an invalid timestamp')
    # EIP-1898 pins the state read to this exact canonical block, including across reorgs.
    block = {'blockHash': latest['hash'], 'requireCanonical': True}
    balance, code = batch([
        ('eth_getBalance', [latest['miner'], block]),
        ('eth_getCode', [latest['miner'], block])])
    if not isinstance(balance, str) or not balance.startswith('0x'):
        raise ValueError('invalid balance response')
    int(balance, 16)
    if not isinstance(code, str) or not code.startswith('0x'):
        raise ValueError('invalid code response')
    bytes.fromhex(code[2:])
    return {'height': int(latest['number'], 16), 'hash': latest['hash'],
            'age_seconds': round(age, 1), 'genesis': genesis['hash']}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != '/healthz':
            self.send_error(404)
            return
        try:
            check_ready()
            status, body = 200, b'rpc-ready'
        except Exception as error:
            logging.warning('RPC not ready: %s', error)
            status, body = 503, b'rpc-not-ready'
        self.send_response(status)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if args.check:
        print(json.dumps(check_ready()))
    else:
        ThreadingHTTPServer(('127.0.0.1', 18545), Handler).serve_forever()


if __name__ == '__main__':
    main()
