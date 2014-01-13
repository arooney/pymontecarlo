#!/usr/bin/env python
"""
================================================================================
:mod:`beam` -- Parameters of the electron beam
================================================================================

.. module:: beam
   :synopsis: Parameters of the electron beam

.. inheritance-diagram:: pymontecarlo.input.beam

"""

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2011 Philippe T. Pinard"
__license__ = "GPL v3"

__all__ = ['PencilBeam',
            'GaussianBeam',
            'tilt_beam',
            'convert_diameter_fwhm_to_sigma',
            'convert_diameter_sigma_to_fwhm']

# Standard library modules.
import math

# Third party modules.
import numpy as np

# Local modules.
from pymontecarlo.options.parameter import \
    (ParameterizedMetaClass, Parameter, AngleParameter, UnitParameter,
     SimpleValidator, EnumValidator, CastValidator)
from pymontecarlo.util.mathutil import vector3d

from pymontecarlo.options.xmlmapper import \
    mapper, ParameterizedAttribute, ParameterizedElement, PythonType, UserType
from pymontecarlo.options.particle import ParticleType

# Globals and constants variables.
from pymontecarlo.options.particle import ELECTRON, PARTICLES

class _Beam(object):

    __metaclass__ = ParameterizedMetaClass

_energy_validator = SimpleValidator(lambda e: e > 0.0,
                                    "Energy must be greater than 0 eV.")
_aperture_validator = SimpleValidator(lambda x: 0.0 <= x <= math.pi / 2,
                                      "Aperture must be between [0, pi/2] rad")

class PencilBeam(_Beam):

    energy = UnitParameter('eV', _energy_validator,
                          "Initial energy of the particle(s)")
    particle = Parameter(EnumValidator(PARTICLES),
                         "Type of particles (see :mod:`.particle`)")
    origin = UnitParameter('m', CastValidator(vector3d),
                           """Initial location of the particle(s).
                             Location saved as a tuple of length 3 for the x, y and z spatial coordinates.""")
    direction = Parameter(CastValidator(vector3d),
                          """Direction of the particle(s).
                          Direction is represented by a tuple of length 3 for the x, y and z coordinates.""")
    aperture = AngleParameter(_aperture_validator,
                              "Angular aperture of the electron beam")

    def __init__(self, energy_eV, particle=ELECTRON,
                 origin_m=(0, 0, 1), direction=(0, 0, -1),
                 aperture_rad=0.0):
        """
        Creates a new pencil beam.
        A pencil beam is a one dimensional beam (no width).

        :arg energy_eV: initial energy of the particle(s)
        :arg particle: type of particles (see :mod:`.particle`).
            [default: :data:`.ELECTRON`]
        :type particle: :class:`_Particle`:
        :arg origin_m: initial location of the particle(s).
            Location saved as a tuple of length 3 for the x, y and z
            spatial coordinates. [default: ``(0, 0, 1)``]
        :arg direction: direction of the particle(s).
            Direction is represented by a tuple of length 3 for the x, y and
            z coordinates. [default: ``(0, 0, -1)``]
        :arg aperture_rad: angular aperture of the electron beam
            [default: ``0.0``]
        """
        self.energy_eV = energy_eV
        self.particle = particle
        self.origin_m = origin_m
        self.direction = direction
        self.aperture_rad = aperture_rad

    def __repr__(self):
        return '<PencilBeam(particle=%s, energy=%s eV, origin=%s m, direction=%s, aperture=%s rad)>' % \
            (self.particle, self.energy_eV, self.origin_m, self.direction, self.aperture_rad)

    @property
    def direction_polar_rad(self):
        """
        Angle of the beam with respect to the positive z-axis. (read-only)
        """
        norm = np.linalg.norm(self.direction)
        return math.acos(self.direction[2] / norm);

    @property
    def direction_azimuth_rad(self):
        """
        Angle of the beam with respect to the positive x-axis in the x-y plane.  (read-only)
        """
        return math.atan2(self.direction[1], self.direction[0]);

mapper.register(PencilBeam, '{http://pymontecarlo.sf.net}pencilBeam',
                ParameterizedAttribute('energy_eV', PythonType(float), 'energy'),
                ParameterizedAttribute('particle', ParticleType()),
                ParameterizedElement('origin_m', UserType(vector3d), 'origin'),
                ParameterizedElement('direction', UserType(vector3d)),
                ParameterizedAttribute('aperture_rad', PythonType(float), 'aperture'))

_diameter_validator = \
    SimpleValidator(lambda d: d >= 0, "Diameter must be equal or greater than 0")

class GaussianBeam(PencilBeam):

    diameter = UnitParameter("m", _diameter_validator,
                             "Diameter of this electron beam equal to the full width at half maximum of a 2D-Gaussian distribution")

    def __init__(self, energy_eV, diameter_m, particle=ELECTRON,
                 origin_m=(0, 0, 1), direction=(0, 0, -1), aperture_rad=0.0):
        """
        Creates a new Gaussian beam.
        A Gaussian beam is a two dimensional beam where the particles are
        distributed following a 2D-Gaussian distribution.

        :arg energy_eV: initial energy of the particle(s)
        :arg diameter_m: diameter of the beam.
            The diameter corresponds to the full width at half maximum (FWHM) of
            a two dimensional Gaussian distribution.
        :arg particle: type of particles (see :mod:`particle`). [default: ``ELECTRON``]
        :type particle: :class:`_Particle`:
        :arg origin_m: initial location of the particle(s).
            Location saved as a tuple of length 3 for the x, y and z
            spatial coordinates. [default: ``(0, 0, 1)``]
        :arg direction: direction of the particle(s).
            Direction is represented by a tuple of length 3 for the x, y and
            z coordinates. [default: ``(0, 0, -1)``]
        :arg aperture_rad: angular aperture of the electron beam
            [default: ``0.0``]
        """
        PencilBeam.__init__(self, energy_eV, particle, origin_m, direction, aperture_rad)

        self.diameter_m = diameter_m

    def __repr__(self):
        return '<GaussianBeam(particle=%s, energy=%s eV, diameter=%s m, origin=%s m, direction=%s, aperture=%s rad)>' % \
            (self.particle, self.energy_eV, self.diameter_m, self.origin_m, self.direction, self.aperture_rad)

mapper.register(GaussianBeam, '{http://pymontecarlo.sf.net}gaussianBeam',
                ParameterizedAttribute('diameter_m', PythonType(float), 'diameter'))

def tilt_beam(angle_rad, axis='y', direction=(0, 0, -1)):
    """
    Returns the direction of the beam after being tilted by an *angle* along
    the specified *axis* of rotation from its original *direction*.

    :arg angle_rad: angle of rotation in radians
    :arg axis: axis of rotation, either ``x``, ``y``, ``z``
    :arg direction: original direction of the beam

    :return: a 3-length :class:`tuple`
    """
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)

    if axis.lower() == 'x':
        r = np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    elif axis.lower() == 'y':
        r = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    elif axis.lower() == 'z':
        r = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    else:
        raise ValueError, "Unknown axis: %s" % axis

    return np.dot(r, direction)

def convert_diameter_fwhm_to_sigma(diameter):
    """
    Converts a beam diameter expressed as 2-sigma of a Gaussian distribution
    (radius = sigma) to a beam diameter expressed as the full with at half
    maximum (FWHM).

    :arg diameter: FWHM diameter.
    """
    # d_{FWHM} = 1.177411 (2\sigma)
    return diameter / 1.177411

def convert_diameter_sigma_to_fwhm(diameter):
    """
    Converts a beam diameter expressed as the full with at half maximum (FWHM)
    to a beam diameter expressed as 2-sigma of a Gaussian distribution
    (radius = sigma).

    :arg diameter: 2-sigma diameter diameter.
    """
    # d_{FWHM} = 1.177411 (2\sigma)
    return diameter * 1.177411