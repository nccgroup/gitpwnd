import unittest
from unittest import TestCase
import json
import os

class TestIntelHelper(TestCase):
    def get_sample_intel(self):
        sample_intel_path = os.path.join(os.path.dirname(__file__), "sample_intel.json")
        with open(sample_intel_path, 'r') as f:
            return json.load(f)

    def test_parse_node_dir(self):
        sample_intel = self.get_sample_intel()
        intel_keys = sample_intel.keys()

        for k in ['ps_services', 'mac_address', 'time_ran', 'whoami', 'python_version', 'ifconfig',
                  'service_configs', 'username', 'env']:
            assert k in intel_keys

if __name__ == '__main__':
    unittest.main()
