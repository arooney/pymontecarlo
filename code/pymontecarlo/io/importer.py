#!/usr/bin/env python
"""
================================================================================
:mod:`importer` -- Base class for all importers
================================================================================

.. module:: importer
   :synopsis: Base class for all importers

.. inheritance-diagram:: pymontecarlo.result.base.importer

"""

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2011 Philippe T. Pinard"
__license__ = "GPL v3"

# Standard library modules.
import warnings

# Third party modules.

# Local modules.
from pymontecarlo.result.results import Results

# Globals and constants variables.

class ImporterWarning(Warning):
    pass

class ImporterException(Exception):
    pass

class Importer(object):

    def __init__(self):
        self._detector_importers = {}

    def _import_results(self, options, *args):
        results = {}

        for name, detector in options.detectors.iteritems():
            clasz = detector.__class__
            method = self._detector_importers.get(clasz)

            if method:
                result = method(options, name, detector, *args)
                results[name] = result
            else:
                message = "Could not import results from '%s' detector (%s)" % \
                    (name, clasz.__name__)
                warnings.warn(message, ImporterWarning)

        return Results(options, results)
