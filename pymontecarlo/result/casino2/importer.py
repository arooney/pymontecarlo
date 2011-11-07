#!/usr/bin/env python
"""
================================================================================
:mod:`importer` -- Casino 2 results importer
================================================================================

.. module:: importer
   :synopsis: Casino 2 results importer

.. inheritance-diagram:: pymontecarlo.result.casino2.importer

"""

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2011 Philippe T. Pinard"
__license__ = "GPL v3"

# Standard library modules.

# Third party modules.

# Local modules.
from pymontecarlo.result.base.importer import Importer
from pymontecarlo.result.base.result import \
    PhotonIntensityResult, create_intensity_dict
from pymontecarlo.input.base.detector import \
    (
#     BackscatteredElectronEnergyDetector,
#     BackscatteredElectronPolarAngularDetector,
#     PhiRhoZDetector,
     PhotonIntensityDetector,
#     TransmittedElectronEnergyDetector,
     )
from pymontecarlo.util.transition import K_family, LIII, MV

from casinoTools.FileFormat.casino2.File import File

# Globals and constants variables.
from casinoTools.FileFormat.casino2.Element import \
    LINE_K, LINE_L, LINE_M, GENERATED, EMITTED

class Casino2Importer(Importer):

    def __init__(self):
        Importer.__init__(self)

        self._detector_importers[PhotonIntensityDetector] = \
            self._detector_photon_intensity_detector

    def import_from_cas(self, options, filepath):
        # Read cas
        casfile = File()
        casfile.readFromFilepath(filepath)

        simresults = casfile.getResultsFirstSimulation()

        return self._import_results(options, simresults)

    def _detector_photon_intensity_detector(self, options, name, detector, simresults):
        regionops = simresults.getRegionOptions()

        factor = detector.solid_angle / (0.0025 * 1e9)

        intensities = {}
        for region in regionops._regions:
            for element in region._elements:
                z = element.getAtomicNumber()
                data = element.getTotalXrayIntensities()

                for line, transitions in [(LINE_K, K_family), (LINE_L, LIII), (LINE_M, MV)]:
                    if line in data:
                        transition = transitions(z)
                        datum = data[line]

                        gt = (datum[GENERATED] * factor, 0.0)
                        et = (datum[EMITTED] * factor, 0.0)

                        tmpints = create_intensity_dict(transition,
                                                        gnf=gt, gt=gt,
                                                        enf=et, et=et)
                        intensities.update(tmpints)

        return PhotonIntensityResult(detector, intensities)


