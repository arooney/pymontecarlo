#!/usr/bin/env python
""" """

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2011 Philippe T. Pinard"
__license__ = "GPL v3"

# Standard library modules.
import unittest
import logging
import tempfile
import shutil
import warnings

# Third party modules.

# Local modules.
from pymontecarlo.testcase import TestCase

from pymontecarlo.input.options import Options
from pymontecarlo.input.limit import ShowersLimit
from pymontecarlo.input.detector import TrajectoryDetector
from pymontecarlo.program.penshower.input.converter import Converter
from pymontecarlo.program.penshower.io.exporter import Exporter

# Globals and constants variables.

warnings.simplefilter("always")

class TestPenelopeExporter(TestCase):

    def setUp(self):
        TestCase.setUp(self)

        self.tmpdir = tempfile.mkdtemp()

        self.c = Converter()
        self.e = Exporter()

    def tearDown(self):
        TestCase.tearDown(self)

        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def testskeleton(self):
        self.assertTrue(True)

    def testexport(self):
        # Create
        ops = Options(name='test1')
        ops.beam.energy_eV = 30e3
        ops.detectors['trajectories'] = TrajectoryDetector(100)
        ops.limits.add(ShowersLimit(100))

        # Export
        self.c.convert(ops)
        self.e.export(ops, self.tmpdir)

if __name__ == '__main__': #pragma: no cover
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()
