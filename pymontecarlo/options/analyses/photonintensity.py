"""
Analysis to record photon intensity emitted towards a detector.
"""

# Standard library modules.

# Third party modules.

# Local modules.
from pymontecarlo.options.analyses.photon import PhotonAnalysis

# Globals and constants variables.

class PhotonIntensityAnalysis(PhotonAnalysis):

    def __init__(self, photon_detector):
        super().__init__(photon_detector)

    def apply(self, options):
        return []

    def calculate(self, simulation, simulations):
        pass
