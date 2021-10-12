#!/usr/bin/python

import unittest
from redmine_exporter import RedmineCollector


class RedmineCollectorTestCase(unittest.TestCase):
    # The build statuses we want to export about.
    # TODO: add more test cases

    def test_prometheus_metrics(self):
        exporter = RedmineCollector('', '', '', False)
        self.assertFalse(hasattr(exporter, '_prometheus_metrics'))

        exporter._setup_empty_prometheus_metrics()
        self.assertTrue(hasattr(exporter, '_prometheus_metrics'))
        self.assertEqual(sorted(exporter._prometheus_metrics.keys()), sorted(RedmineCollector.apimetrics))


if __name__ == "__main__":
    unittest.main()
