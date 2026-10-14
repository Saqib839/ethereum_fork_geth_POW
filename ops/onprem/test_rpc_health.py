"""Exercise readiness failure conditions without changing a running node."""
import copy
import time
import unittest
from unittest.mock import patch

import rpc_health as health


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.block = {'number': '0x10', 'hash': '0x' + 'ab' * 32,
                      'miner': '0x' + '12' * 20, 'timestamp': hex(int(time.time()))}
        self.identity = ['0x14ec', {'hash': health.GENESIS}, False, self.block]

    def test_ready_reads_state_at_exact_canonical_hash(self):
        with patch.object(health, 'batch', side_effect=[self.identity, ['0x0', '0x']]) as rpc:
            self.assertEqual(health.check_ready()['height'], 16)
        state_calls = rpc.call_args_list[1].args[0]
        self.assertEqual(state_calls[0][1][1],
                         {'blockHash': self.block['hash'], 'requireCanonical': True})

    def test_identity_sync_and_timestamp_failures(self):
        cases = []
        for index, value in [(0, '0x1'), (1, {'hash': '0x00'}), (2, {}), (2, True)]:
            case = copy.deepcopy(self.identity)
            case[index] = value
            cases.append(case)
        for stamp in (time.time() - health.MAX_AGE - 1, time.time() + 60):
            case = copy.deepcopy(self.identity)
            case[3]['timestamp'] = hex(int(stamp))
            cases.append(case)
        case = copy.deepcopy(self.identity)
        case[3]['number'] = '0x0'
        cases.append(case)
        for case in cases:
            with self.subTest(case=case), patch.object(health, 'batch', return_value=case):
                with self.assertRaises(ValueError):
                    health.check_ready()

    def test_state_errors_fail_closed(self):
        for state in ([None, '0x'], ['0x0', None], ['0x0', 'invalid'], ['invalid', '0x']):
            with self.subTest(state=state), patch.object(
                    health, 'batch', side_effect=[self.identity, state]):
                with self.assertRaises(ValueError):
                    health.check_ready()
        with patch.object(health, 'batch', side_effect=[self.identity, OSError('state unavailable')]):
            with self.assertRaises(OSError):
                health.check_ready()


if __name__ == '__main__':
    unittest.main()
