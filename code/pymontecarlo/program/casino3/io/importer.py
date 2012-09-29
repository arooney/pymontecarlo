#!/usr/bin/env python
"""
================================================================================
:mod:`importer` -- Casino 3 importer
================================================================================

.. module:: Casino 3
   :synopsis: PENEPMA importer

.. inheritance-diagram:: pymontecarlo.program.casino3.io.importer

"""

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2012 Philippe T. Pinard"
__license__ = "GPL v3"

# Standard library modules.

# Third party modules.
import numpy as np

# Local modules.
from casinoTools.FileFormat.casino3.File import File

from pymontecarlo.output.result import TrajectoryResult, Trajectory
from pymontecarlo.input.particle import ELECTRON
from pymontecarlo.input.collision import NO_COLLISION, DELTA, HARD_INELASTIC
from pymontecarlo.input.detector import TrajectoryDetector

from pymontecarlo.io.importer import Importer as _Importer

# Globals and constants variables.
from pymontecarlo.output.result import \
    EXIT_STATE_ABSORBED, EXIT_STATE_BACKSCATTERED, EXIT_STATE_TRANSMITTED
from casinoTools.FileFormat.casino3.TrajectoryCollision import \
    (COLLISION_TYPE_ATOM, COLLISION_TYPE_REGION,
     COLLISION_TYPE_NODE, COLLISION_TYPE_RECALC)

_COLLISIONS_REF = {COLLISION_TYPE_ATOM: HARD_INELASTIC,
                   COLLISION_TYPE_REGION: DELTA,
                   COLLISION_TYPE_NODE: DELTA,
                   COLLISION_TYPE_RECALC: NO_COLLISION}

class Importer(_Importer):

    def __init__(self):
        _Importer.__init__(self)

        self._detector_importers[TrajectoryDetector] = self._detector_trajectory

    def import_from_cas(self, options, filepath):
        # Read cas
        casfile = File(filepath)

        simdata = casfile.getFirstSimulation()

        return self._import_results(options, simdata)

    def _detector_trajectory(self, options, key, detector, simdata, *args):
        trajectories = []

        for traj in simdata.getFirstScanPointResults().getSavedTrajectories():
            primary = not traj.isTypeSecondary()

            particle = ELECTRON

            if traj.isTypeBackscattered():
                exit_state = EXIT_STATE_BACKSCATTERED
            elif traj.isTypeTransmitted():
                exit_state = EXIT_STATE_TRANSMITTED
            else:
                exit_state = EXIT_STATE_ABSORBED

            collision = _COLLISIONS_REF.get(traj.getScatteringEvent(0).getCollisionType(), NO_COLLISION)

            interactions = np.zeros((traj.getNumberScatteringEvents(), 5))
            for i, event in enumerate(traj.getScatteringEvents()):
                interactions[i, 0] = event.getX_nm() * 1e-9 # m
                interactions[i, 1] = event.getY_nm() * 1e-9 # m
                interactions[i, 2] = event.getZ_nm() * 1e-9 # m
                interactions[i, 3] = event.getEnergy_keV() * 1000.0 # eV
                interactions[i, 4] = int(_COLLISIONS_REF.get(event.getCollisionType(), NO_COLLISION))

            trajectories.append(Trajectory(primary, particle, collision,
                                           exit_state, interactions))

        return TrajectoryResult(trajectories)

