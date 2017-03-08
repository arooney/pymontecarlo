#!/usr/bin/env python
""" """

# Standard library modules.
import unittest
import logging

# Third party modules.

# Local modules.
from pymontecarlo.testcase import TestCase, WorkerMock

# Globals and constants variables.

class TestWorker(TestCase):

    def setUp(self):
        super().setUp()

        self.w = WorkerMock()

    def testrun(self):
        options = self.create_basic_options()
        simulation = self.w.run(options)

        self.assertAlmostEqual(1.0, self.w.progress)
        self.assertEqual('Done', self.w.status)
        self.assertEqual(simulation.options, options)

if __name__ == '__main__': #pragma: no cover
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()
