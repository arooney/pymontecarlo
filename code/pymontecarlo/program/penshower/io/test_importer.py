#!/usr/bin/env python
""" """

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2012 Philippe T. Pinard"
__license__ = "GPL v3"

# Standard library modules.
import unittest
import logging
import os

# Third party modules.

# Local modules.
from pymontecarlo.testcase import TestCase

from pymontecarlo.input.options import Options
from pymontecarlo.input.detector import TrajectoryDetector
from pymontecarlo.program.penshower.io.importer import Importer

import DrixUtilities.Files as Files

# Globals and constants variables.
from pymontecarlo.input.particle import ELECTRON
from pymontecarlo.input.collision import NO_COLLISION
from pymontecarlo.output.result import EXIT_STATE_ABSORBED

class TestImporter(TestCase):

    def setUp(self):
        TestCase.setUp(self)

        relativePath = os.path.join('../testdata/test1')
        self.testdata = Files.getCurrentModulePath(__file__, relativePath)

        self.i = Importer()

    def tearDown(self):
        TestCase.tearDown(self)

    def testskeleton(self):
        self.assertTrue(True)

    def test_detector_trajectory(self):
        # Create
        ops = Options(name='test1')
        ops.beam.energy_eV = 20e3
        ops.detectors['trajectories'] = TrajectoryDetector(50)

        # Import
        results = self.i.import_from_dir(ops, self.testdata)

        # Test
        result = results['trajectories']
        self.assertEqual(559, len(result))

        trajectory = list(result)[0]
        self.assertTrue(trajectory.is_primary())
        self.assertFalse(trajectory.is_secondary())
        self.assertIs(ELECTRON, trajectory.particle)
        self.assertIs(NO_COLLISION, trajectory.collision)
        self.assertEqual(EXIT_STATE_ABSORBED, trajectory.exit_state)
        self.assertEqual(577, len(trajectory.interactions))
        self.assertEqual(5, trajectory.interactions.shape[1])

if __name__ == '__main__': #pragma: no cover
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()
