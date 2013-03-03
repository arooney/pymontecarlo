#!/usr/bin/env python
"""
================================================================================
:mod:`result` -- Simulation results
================================================================================

.. module:: result
   :synopsis: Simulation results

.. inheritance-diagram:: pymontecarlo.output.result

"""

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2011 Philippe T. Pinard"
__license__ = "GPL v3"

# Standard library modules.
import bisect
from math import sqrt
from collections import Iterable, Sized

# Third party modules.
import numpy as np

# Local modules.
from pymontecarlo.util.transition import from_string
from pymontecarlo.output.manager import ResultManager

import pymontecarlo.util.progress as progress

# Globals and constants variables.
from pymontecarlo.input.particle import PARTICLES
from pymontecarlo.input.collision import COLLISIONS

GENERATED = "g"
EMITTED = "e"
NOFLUORESCENCE = "nf"
CHARACTERISTIC = "cf"
BREMSSTRAHLUNG = "bf"
TOTAL = "t"

class _Result(object):
    """
    Base class of all results. 
    A result is a read-only class where results of a detector are stored.
    
    Derived classes must implement :meth:`__loadzip__` and :meth:`__savezip__`
    which respectively load and save the result to a ZIP file.
    
    Each result class must be register in the ResultManager.
    """

    @classmethod
    def __loadzip__(cls, zipfile, key):
        return cls()

    @classmethod
    def __loadhdf5__(cls, hdf5file, key):
        return cls()

    def __savehdf5__(self, hdf5file, key):
        pass

def create_intensity_dict(transition,
                          gcf=(0.0, 0.0), gbf=(0.0, 0.0), gnf=(0.0, 0.0), gt=(0.0, 0.0),
                          ecf=(0.0, 0.0), ebf=(0.0, 0.0), enf=(0.0, 0.0), et=(0.0, 0.0)):
    return {transition: {
                GENERATED: {
                    CHARACTERISTIC: gcf,
                    BREMSSTRAHLUNG: gbf,
                    NOFLUORESCENCE: gnf,
                    TOTAL: gt},
                EMITTED: {
                    CHARACTERISTIC: ecf,
                    BREMSSTRAHLUNG: ebf,
                    NOFLUORESCENCE: enf,
                    TOTAL: et}
                         }
            }

class PhotonIntensityResult(_Result):

    def __init__(self, intensities={}):
        """
        Creates a new result to store photon intensities.
        
        :arg intensities: :class:`dict` containing the intensities.
            One should use :func:`.create_intensity_dict` to create the dictionary
        """
        _Result.__init__(self)

        # Check structure
        def _check1(transition, data, key1, name1):
            if key1 not in data:
                raise ValueError, "Transition %s is missing %s intensities" % \
                        (transition, name1)

        def _check2(transition, data, key1, name1, key2, name2):
            if key2 not in data[key1]:
                raise ValueError, "Transition %s is missing %s %s intensities" % \
                        (transition, name1, name2)

            if len(data[key1][key2]) != 2:
                raise ValueError, 'Intensity for %s %s %s must be a tuple (value, uncertainty)' % \
                    (transition, name1, name2)

        for transition, data in intensities.iteritems():
            _check1(transition, data, GENERATED, 'generated')
            _check1(transition, data, EMITTED, 'emitted')

            _check2(transition, data, GENERATED, 'generated', CHARACTERISTIC, 'characteristic')
            _check2(transition, data, GENERATED, 'generated', BREMSSTRAHLUNG, 'bremsstrahlung')
            _check2(transition, data, GENERATED, 'generated', NOFLUORESCENCE, 'no fluorescence')
            _check2(transition, data, GENERATED, 'generated', TOTAL, 'total')

            _check2(transition, data, EMITTED, 'emitted', CHARACTERISTIC, 'characteristic')
            _check2(transition, data, EMITTED, 'emitted', BREMSSTRAHLUNG, 'bremsstrahlung')
            _check2(transition, data, EMITTED, 'emitted', NOFLUORESCENCE, 'no fluorescence')
            _check2(transition, data, EMITTED, 'emitted', TOTAL, 'total')

        self._intensities = intensities

    @classmethod
    def __loadhdf5__(cls, hdf5file, key):
        hdf5group = hdf5file[key]

        intensities = {}

        for transition, dataset in hdf5group.iteritems():
            transition = from_string(str(transition))

            gcf = dataset.attrs['gcf']
            gbf = dataset.attrs['gbf']
            gnf = dataset.attrs['gnf']
            gt = dataset.attrs['gt']

            ecf = dataset.attrs['ecf']
            ebf = dataset.attrs['ebf']
            enf = dataset.attrs['enf']
            et = dataset.attrs['et']

            intensities.update(create_intensity_dict(transition,
                                                     gcf, gbf, gnf, gt,
                                                     ecf, ebf, enf, et))

        return cls(intensities)

    def __savehdf5__(self, hdf5file, key):
        hdf5group = hdf5file.require_group(key)

        for transition, intensities in self._intensities.iteritems():
            dataset = hdf5group.create_dataset(str(transition), shape=())

            dataset.attrs['gcf'] = intensities[GENERATED][CHARACTERISTIC]
            dataset.attrs['gbf'] = intensities[GENERATED][BREMSSTRAHLUNG]
            dataset.attrs['gnf'] = intensities[GENERATED][NOFLUORESCENCE]
            dataset.attrs['gt'] = intensities[GENERATED][TOTAL]

            dataset.attrs['ecf'] = intensities[EMITTED][CHARACTERISTIC]
            dataset.attrs['ebf'] = intensities[EMITTED][BREMSSTRAHLUNG]
            dataset.attrs['enf'] = intensities[EMITTED][NOFLUORESCENCE]
            dataset.attrs['et'] = intensities[EMITTED][TOTAL]

    def __contains__(self, transition):
        return self.has_intensity(transition)

    def _get_intensity(self, key, transition, absorption=True):
        if isinstance(transition, basestring):
            transition = from_string(transition)

        # Get intensity data
        data = []
        if isinstance(transition, Iterable): # transitionset
            if transition in self._intensities:
                data.append(self._intensities[transition])
            else:
                for t in transition:
                    if t in self._intensities: # Add only known transitions
                        data.append(self._intensities[t])

            if not data:
                raise ValueError, "No intensity for transition(s): %s" % transition
        else: # single transition
            try:
                data.append(self._intensities[transition])
            except KeyError:
                raise ValueError, "No intensity for transition(s): %s" % transition

        # Retrieve intensity (and its uncertainty)
        absorption_key = EMITTED if absorption else GENERATED

        total_val = 0.0
        total_unc = 0.0
        for datum in data:
            val, unc = datum[absorption_key][key]
            total_val += val
            total_unc += unc ** 2

        total_unc = sqrt(total_unc)

        return total_val, total_unc

    def has_intensity(self, transition):
        """
        Returns whether the result contains an intensity for the specified 
        transition.
        
        :arg transition: transition or set of transitions or name of the
            transition or transitions set (see examples in :meth:`.intensity`)
        """
        if isinstance(transition, basestring):
            transition = from_string(transition)

        # Get intensity data
        data = []
        if isinstance(transition, Iterable): # transitionset
            if transition in self._intensities:
                data.append(self._intensities[transition])
            else:
                for t in transition:
                    if t in self._intensities: # Add only known transitions
                        data.append(self._intensities[t])

            if not data:
                return False
        else: # single transition
            if not self._intensities.has_key(transition):
                return False

        return True

    def intensity(self, transition, absorption=True, fluorescence=True):
        """
        Returns the intensity (and its uncertainty) in counts / (sr.electron).
        
        These examples will all returned the same values::
        
            >>> result.intensity(Transition(13, 4, 1))
            >>> result.intensity('Al Ka1')
        
        or
        
            >>> result.intensity(K_family(13))
            >>> result.intensity('Al K')
            
        Note that in the case of a set of transitions (e.g. family, shell),
        the intensity of each transition in the set is added. 
        For instance, the following lines will yield the same result::
        
            >>> result.intensity('Al Ka1')[0] + result.intensity('Al Ka2')[0]
            >>> result.intensity('Al Ka')[0]
            
        Note that the ``[0]`` is to return the intensity part of the 
        intensity/uncertainty tuple.
        
        :arg transition: transition or set of transitions or name of the
            transition or transitions set (see examples)
        :arg absorption: whether to return the intensity with absorption.
            If ``True``, emitted intensity is returned, if ``false`` generated
            intensity.
        :arg fluorescence: whether to return the intensity with fluorescence.
            If ``True``, intensity with fluorescence is returned, if ``false``
            intensity without fluorescence.
            
        :return: intensity and its uncertainty
        :raise: :class:`ValueError` if there is no intensity for the specified
            transition
        """
        key = TOTAL if fluorescence else NOFLUORESCENCE
        return self._get_intensity(key, transition, absorption)

    def characteristic_fluorescence(self, transition, absorption=True):
        """
        Returns the intensity (and its uncertainty) of the characteristic photons
        produced by fluorescence of primary photons in counts / (sr.electron).
        
        :arg transition: transition or set of transitions or name of the
            transition or transitions set (see examples in :meth:`.intensity`)
        :arg absorption: whether to return the intensity with absorption.
            If ``True``, emitted intensity is returned, if ``false`` generated
            intensity.
            
        :return: intensity and its uncertainty
        :raise: :class:`ValueError` if there is no intensity for the specified
            transition
        """
        return self._get_intensity(CHARACTERISTIC, transition, absorption)

    def bremsstrahlung_fluorescence(self, transition, absorption=True):
        """
        Returns the intensity (and its uncertainty) of the Bremsstrahlung photons
        produced by fluorescence of primary photons in counts / (sr.electron).
        
        :arg transition: transition or set of transitions or name of the
            transition or transitions set (see examples in :meth:`.intensity`)
        :arg absorption: whether to return the intensity with absorption.
            If ``True``, emitted intensity is returned, if ``false`` generated
            intensity.
            
        :return: intensity and its uncertainty
        :raise: :class:`ValueError` if there is no intensity for the specified
            transition
        """
        return self._get_intensity(BREMSSTRAHLUNG, transition, absorption)

    def fluorescence(self, transition, absorption=True):
        """
        Returns the intensity (and its uncertainty) of the fluorescence 
        contribution to the total intensity in counts / (sr.electron).
        
        :arg transition: transition or set of transitions or name of the
            transition or transitions set (see examples in :meth:`.intensity`)
        :arg fluorescence: whether to return the intensity with fluorescence.
            If ``True``, intensity with fluorescence is returned, if ``false``
            intensity without fluorescence.
            
        :return: intensity and its uncertainty
        :raise: :class:`ValueError` if there is no intensity for the specified
            transition
        """
        # Note: TOTAL - FLUORESCENCE should be equal to CHARACTERISTIC + BREMSS
        v1, e1 = self._get_intensity(NOFLUORESCENCE, transition, absorption)
        v2, e2 = self._get_intensity(TOTAL, transition, absorption)

        return v2 - v1, e1 + e2

    def absorption(self, transition, fluorescence=True):
        """
        Returns the intensity (and its uncertainty) of the absorption 
        contribution to the total intensity in counts / (sr.electron).
        
        :arg transition: transition or set of transitions or name of the
            transition or transitions set (see examples in :meth:`.intensity`)
        :arg absorption: whether to return the intensity with absorption.
            If ``True``, emitted intensity is returned, if ``false`` generated
            intensity.
            
        :return: intensity and its uncertainty
        :raise: :class:`ValueError` if there is no intensity for the specified
            transition
        """
        v1, e1 = self.intensity(transition, absorption=False, fluorescence=fluorescence)
        v2, e2 = self.intensity(transition, absorption=True, fluorescence=fluorescence)

        return v2 - v1, e1 + e2

    def iter_transitions(self, absorption=True, fluorescence=True):
        """
        Returns an iterator returning a tuple of the transition and intensity.
        
        :arg absorption: whether to return the intensity with absorption.
            If ``True``, emitted intensity is returned, if ``false`` generated
            intensity.
        :arg fluorescence: whether to return the intensity with fluorescence.
            If ``True``, intensity with fluorescence is returned, if ``false``
            intensity without fluorescence.
        """
        for transition in self._intensities:
            yield transition, self.intensity(transition, absorption, fluorescence)

ResultManager.register('PhotonIntensityResult', PhotonIntensityResult)

class PhotonSpectrumResult(_Result):

    def __init__(self, total, background):
        """
        Stores results from a photon spectrum.
        
        All intensities are given in counts / (sr.eV.electron). 
        In other words, the number of counts is normalized by the solid angle 
        of the detector collecting the spectrum, the width of the energy 
        channel and the number of simulated electrons.
        
        :arg total: numpy array containing 2 or 3 columns. The first column
            must be the mid-energy of each bin in eV, the second, the total intensity
            in counts/(sr.eV.electron) and the third (optional), the
            uncertainty on the total intensity.
            
        :arg background: numpy array containing 2 or 3 columns. The first column
            must be the mid-energy of each bin, the second, the background
            intensity in counts/(sr.eV.electron) and the third (optional), the
            uncertainty on the background intensity.
            
        .. note::
        
           The first column of the total and background arrays must be equal.
        """
        def _check(data):
            if data.shape[1] < 2:
                raise ValueError, 'The data must contains at least two columns'
            if data.shape[1] == 2:
                data = np.append(data, np.zeros((data.shape[0], 1)), 1)

            return data

        if not np.allclose(total[:, 0], background[:, 0]):
            raise ValueError, 'Energies are different for the total and background array'

        _Result.__init__(self)

        self._total = _check(total)
        self._background = _check(background)

    @classmethod
    def __loadhdf5__(cls, hdf5file, key):
        hdf5group = hdf5file[key]
        total = np.copy(hdf5group['total'])
        background = np.copy(hdf5group['background'])
        return cls(total, background)

    def __savehdf5__(self, hdf5file, key):
        hdf5group = hdf5file.require_group(key)
        hdf5group.create_dataset('total', data=self._total)
        hdf5group.create_dataset('background', data=self._background)

    @property
    def energy_channel_width_eV(self):
        """
        Width of each energy channel in eV.
        """
        return self._total[1, 0] - self._total[0, 0]

    @property
    def energy_offset_eV(self):
        """
        Energy offset of the spectrum in eV. 
        """
        return self._total[0, 0]

    def get_total(self):
        """
        Returns a numpy array where the first column is the mid-energy of each 
        bin in eV, the second, the total intensity in counts/(sr.eV.electron) 
        and the third (optional), the uncertainty on the total intensity.
        """
        return np.copy(self._total)

    def get_background(self):
        """
        Returns a numpy array where the first column is the mid-energy of each 
        bin in eV, the second, the background intensity in counts/(sr.eV.electron) 
        and the third (optional), the uncertainty on the background intensity.
        """
        return np.copy(self._background)

    def _get_intensity(self, energy_eV, data):
        """
        Returns the intensity and its uncertainty for the specified 
        energy.
        Returns ``(0.0, 0.0)`` if the energy in outside the range of the 
        spectrum.
    
        :arg energy_eV: energy of interest (in eV).
        :arg values: intensity values
        :arg uncs: uncertainty values
        """
        if energy_eV >= data[-1, 0] + self.energy_channel_width_eV:
            return 0.0, 0.0 # Above last channel

        index = bisect.bisect_right(data[:, 0], energy_eV)
        if not index:
            return 0.0, 0.0 # Below first channel

        return data[index - 1, 1:3]

    def total_intensity(self, energy_eV):
        """
        Returns the total intensity (in counts / (sr.eV.electron) and its 
        uncertainty for the specified energy.
        Returns ``(0.0, 0.0)`` if the energy in outside the range of the 
        spectrum.
    
        :arg energy_eV: energy of interest (in eV).
        """
        return self._get_intensity(energy_eV, self._total)

    def background_intensity(self, energy_eV):
        """
        Returns the background intensity (in counts / (sr.eV.electron) and its 
        uncertainty for the specified energy.
        Returns ``(0.0, 0.0)`` if the energy in outside the range of the 
        spectrum.
    
        :arg energy_eV: energy of interest (in eV).
        """
        return self._get_intensity(energy_eV, self._background)

ResultManager.register('PhotonSpectrumResult', PhotonSpectrumResult)

def create_phirhoz_dict(transition, gnf=None, gt=None, enf=None, et=None):
    """
    Values of *gnf*, *gt*, *enf* and *et* must be a Numpy array containing two
    or three columns:
    
        * :math:`\\rho z` values (in kg/m2)
        * intensities
        * (optional) uncertainties on the intensities
    """
    def _check(data):
        if data.shape[1] < 2:
            raise ValueError, 'The data must contains at least two columns'
        if data.shape[1] == 2:
            data = np.append(data, np.zeros((data.shape[0], 1)), 1)

        return data

    dist = {transition: {}}

    if gnf is not None:
        dist[transition].setdefault(GENERATED, {})[NOFLUORESCENCE] = _check(gnf)
    if gt is not None:
        dist[transition].setdefault(GENERATED, {})[TOTAL] = _check(gt)
    if enf is not None:
        dist[transition].setdefault(EMITTED, {})[NOFLUORESCENCE] = _check(enf)
    if et is not None:
        dist[transition].setdefault(EMITTED, {})[TOTAL] = _check(et)

    return dist

class PhiRhoZResult(_Result):

    def __init__(self, distributions={}):
        """
        Creates a new result to store :math:`\\phi(\\rho z)` distributions.
        
        :arg distributions: :class:`dict` containing the distributions.
            One should use :func:`.create_phirhoz_dict` to create the dictionary
        """
        _Result.__init__(self)
        self._distributions = distributions

    @classmethod
    def __loadhdf5__(cls, hdf5file, key):
        hdf5group = hdf5file[key]

        data = {}
        for transition, group in hdf5group.iteritems():
            transition = from_string(str(transition))

            for suffix, dataset in group.iteritems():
                data.setdefault(transition, {})[suffix] = np.copy(dataset)

        # Construct distributions
        distributions = {}
        for transition, datum in data.iteritems():
            distributions.update(create_phirhoz_dict(transition, **datum))

        return cls(distributions)

    def __savehdf5__(self, hdf5file, key):
        distributions = [('gnf', False, False), ('gt', False, True),
                         ('enf', True, False), ('et', True, True)]

        hdf5group = hdf5file.require_group(key)

        for suffix, absorption, fluorescence in distributions:
            for transition, data in self.iter_transitions(absorption, fluorescence):
                group = hdf5group.require_group(str(transition))
                group.create_dataset(suffix, data=data)

    def exists(self, transition, absorption=True, fluorescence=True):
        """
        Returns whether the result contains a :math:`\\phi(\\rho z)`
        distribution for the specified transition.
        
        :arg transition: transition or set of transitions or name of the
            transition or transitions set (see examples in :meth:`.get`)
        :arg absorption: distribution with absorption. If ``True``, emitted 
            distribution is returned, if ``False`` generated distribution.
        :arg fluorescence: distribution with fluorescence. If ``True``, 
            distribution with fluorescence is returned, if ``False`` 
            distribution without fluorescence.
        """
        if isinstance(transition, basestring):
            transition = from_string(transition)

        if transition not in self._distributions:
            return False

        absorption_key = EMITTED if absorption else GENERATED
        if absorption_key not in self._distributions[transition]:
            return False

        fluorescence_key = TOTAL if fluorescence else NOFLUORESCENCE
        if fluorescence_key not in self._distributions[transition][absorption_key]:
            return False

        return True

    def get(self, transition, absorption=True, fluorescence=True):
        """
        Returns the :math:`\\phi(\\rho z)` distribution for the specified 
        transition.
        A Numpy array is returned where the columns are:
            
            * :math:`\\rho z` values (in kg/m2)
            * intensities
            * uncertainties on the intensities
            
        :arg transition: transition or set of transitions or name of the
            transition or transitions set (see examples)
        :arg absorption: whether to return the distribution with absorption.
            If ``True``, emitted :math:`\\phi(\\rho z)` is returned, 
            if ``False`` generated :math:`\\phi(\\rho z)`.
        :arg fluorescence: whether to return the distribution with fluorescence.
            If ``True``, :math:`\\phi(\\rho z)` with fluorescence is returned, 
            if ``False`` :math:`\\phi(\\rho z)` without fluorescence.
            
        :raise: :class:`ValueError` if there is no distribution for the 
            specified transition.
            
        Here are examples that will all returned the same values::
        
            >>> phirhoz = result.get(Transition(13, 4, 1))
            >>> rzs = phirhoz[:,0]; vals = phirhoz[:,1]
            >>> phirhoz = result.get('Al Ka1')
        
        or
        
            >>> phirhoz = result.get(K_family(13))
            >>> phirhoz = result.get('Al K')
        """
        if isinstance(transition, basestring):
            transition = from_string(transition)

        # Check existence
        if not self.exists(transition, absorption, fluorescence):
            raise ValueError, "No distribution for transition(s): %s" % transition

        # Retrieve data
        absorption_key = EMITTED if absorption else GENERATED
        fluorescence_key = TOTAL if fluorescence else NOFLUORESCENCE

        distribution = \
            self._distributions[transition][absorption_key][fluorescence_key]

        return np.copy(distribution)

    def integral(self, transition, absorption=True, fluorescence=True):
        """
        Returns the integral over the phi-rho-z for the specified transition 
        in kg/m2.
        
        :arg transition: transition or set of transitions or name of the
            transition or transitions set (see examples)
        :arg absorption: whether to use the :math:`\\phi(\\rho z)` with 
            absorption. If ``True``, emitted :math:`\\phi(\\rho z)` is used, 
            if ``False`` generated :math:`\\phi(\\rho z)`.
        :arg fluorescence: whether to use math:`\\phi(\\rho z)` with 
            fluorescence. If ``True``, :math:`\\phi(\\rho z)` with fluorescence 
            is used, if ``False`` :math:`\\phi(\\rho z)` without fluorescence.
            
        :rtype: :class:`float`
        """
        distribution = self.get(transition, absorption, fluorescence)
        rzs = distribution[:, 0]
        vals = distribution[:, 1]
        width = abs(rzs[1] - rzs[0])
        return sum(vals) * width

    def fchi(self, transition, fluorescence=True):
        """
        Returns the ratio between the emitted over the generated phi-rho-zs for 
        the specified transition.
        
        :arg transition: transition or set of transitions or name of the
            transition or transitions set (see examples)
        :arg fluorescence: whether to return the distribution with fluorescence.
            If ``True``, :math:`\\phi(\\rho z)` with fluorescence is used, 
            if ``False`` :math:`\\phi(\\rho z)` without fluorescence.
            
        :rtype: :class:`float`
        """
        Fchi = self.integral(transition, True, fluorescence)
        F0chi = self.integral(transition, False, fluorescence)
        return Fchi / F0chi

    def iter_transitions(self, absorption=True, fluorescence=True):
        """
        Returns an iterator returning a tuple of the:

          * transition
          * depths (in kg/m2)
          * intensities
          * uncertainties on the intensities
        
        :arg absorption: whether to return the distribution with absorption.
            If ``True``, emitted intensity is returned, if ``False`` generated
            intensity.
        :arg fluorescence: whether to return the distribution with fluorescence.
            If ``True``, intensity with fluorescence is returned, if ``False``
            intensity without fluorescence.
        """
        for transition in self._distributions:
            if not self.exists(transition, absorption, fluorescence):
                continue

            distribution = self.get(transition, absorption, fluorescence)
            yield transition, distribution

ResultManager.register('PhiRhoZResult', PhiRhoZResult)

class TimeResult(_Result):

    def __init__(self, simulation_time_s=0.0, simulation_speed_s=(0.0, 0.0)):
        """
        Creates a new result to store simulation time and speed.
        
        :arg simulation_time_s: total time of the simulation (in seconds)
        :arg simulation_speed_s: time to simulation one electron (in seconds) and
            its uncertainty
        """
        _Result.__init__(self)

        self._simulation_time_s = simulation_time_s

        if len(simulation_speed_s) != 2:
            raise ValueError, "Simulation speed must be a tuple (value, uncertainty)"
        self._simulation_speed_s = simulation_speed_s

    @classmethod
    def __loadhdf5__(cls, hdf5file, key):
        hdf5group = hdf5file[key]
        simulation_time_s = hdf5group.attrs['simulation_time_s']
        simulation_speed_s = hdf5group.attrs['simulation_speed_s']

        return cls(simulation_time_s, simulation_speed_s)

    def __savehdf5__(self, hdf5file, key):
        hdf5group = hdf5file.require_group(key)
        hdf5group.attrs['simulation_time_s'] = self.simulation_time_s
        hdf5group.attrs['simulation_speed_s'] = self.simulation_speed_s

    @property
    def simulation_time_s(self):
        return self._simulation_time_s

    @property
    def simulation_speed_s(self):
        return self._simulation_speed_s

ResultManager.register('TimeResult', TimeResult)

class ShowersStatisticsResult(_Result):

    def __init__(self, showers=0):
        """
        Creates a new result to store statistics about the showers.
        
        :arg showers: number of simulated particles
        """
        _Result.__init__(self)

        self._showers = int(showers)

    @classmethod
    def __loadhdf5__(cls, hdf5file, key):
        hdf5group = hdf5file[key]
        showers = hdf5group.attrs['showers']
        return cls(showers)

    def __savehdf5__(self, hdf5file, key):
        hdf5group = hdf5file.require_group(key)
        hdf5group.attrs['showers'] = self.showers

    @property
    def showers(self):
        return self._showers

ResultManager.register('ShowersStatisticsResult', ShowersStatisticsResult)

class ElectronFractionResult(_Result):

    def __init__(self, absorbed=(0.0, 0.0),
                        backscattered=(0.0, 0.0),
                        transmitted=(0.0, 0.0)):
        _Result.__init__(self)

        if len(absorbed) != 2:
            raise ValueError, "Absorbed fraction must be a tuple (value, uncertainty)"
        self._absorbed = absorbed

        if len(backscattered) != 2:
            raise ValueError, "Backscattered fraction must be a tuple (value, uncertainty)"
        self._backscattered = backscattered

        if len(transmitted) != 2:
            raise ValueError, "Transmitted fraction must be a tuple (value, uncertainty)"
        self._transmitted = transmitted

    @classmethod
    def __loadhdf5__(cls, hdf5file, key):
        hdf5group = hdf5file[key]
        absorbed = hdf5group.attrs['absorbed']
        backscattered = hdf5group.attrs['backscattered']
        transmitted = hdf5group.attrs['transmitted']

        return cls(absorbed, backscattered, transmitted)

    def __savehdf5__(self, hdf5file, key):
        hdf5group = hdf5file.require_group(key)
        hdf5group.attrs['absorbed'] = self.absorbed
        hdf5group.attrs['backscattered'] = self.backscattered
        hdf5group.attrs['transmitted'] = self.transmitted

    @property
    def absorbed(self):
        return self._absorbed

    @property
    def backscattered(self):
        return self._backscattered

    @property
    def transmitted(self):
        return self._transmitted

ResultManager.register('ElectronFractionResult', ElectronFractionResult)

EXIT_STATE_TRANSMITTED = 1
EXIT_STATE_BACKSCATTERED = 2
EXIT_STATE_ABSORBED = 3

EXIT_STATES = frozenset([EXIT_STATE_BACKSCATTERED, EXIT_STATE_TRANSMITTED,
                         EXIT_STATE_ABSORBED])

class Trajectory(object):
    def __init__(self, primary, particle, collision, exit_state, interactions):
        """
        Container for one trajectory.
        
        :arg primary: whether the trajectory corresponds to a primary particle
        :type primary: :class:`bool`
        
        :arg particle: type of particle
            (:const:`ELECTRON`, :const:`Photon` or :const:`POSITRON`)
        :type particle: :class:`_Particle`
        
        :arg collision: type of collision that created this trajectory
        :type collision: :class:`_Collision`
        
        :arg exit_state: exit state flag (backscattered, transmitted or absorbed)
        
        :arg interactions: two-dimensional array where each row corresponds
            to an interaction of the particle. The columns are defined as 
            follows:
            
                #. x position (in m)
                #. y position (in m)
                #. z position (in m)
                #. energy at position (in eV)
                #. type of collision
                #. region
            
            The array can contain more columns.
        :type: :class:`ndarray`
        """
        self._primary = primary
        self._particle = particle
        self._collision = collision
        self._exit_state = exit_state
        self._interactions = interactions

    def __repr__(self):
        primary = {True: 'primary', False: 'secondary'}[self._primary]
        particle = str(self._particle).lower()
        collision = str(self._collision)
        exit_state = {EXIT_STATE_ABSORBED: 'absorbed',
                      EXIT_STATE_BACKSCATTERED: 'backscattered',
                      EXIT_STATE_TRANSMITTED: 'transmitted'}.get(self.exit_state)
        interactions_count = len(self.interactions)

        if self.is_primary():
            return '<Trajectory(%s %s %s with %i interactions)>' % \
                (primary, exit_state, particle, interactions_count)
        else:
            return '<Trajectory(%s %s %s from %s with %i interactions)>' % \
                (primary, exit_state, particle, collision, interactions_count)

    @property
    def particle(self):
        """
        Returns the type of particle.
        """
        return self._particle

    @property
    def collision(self):
        """
        Returns the type of collision that created this trajectory.
        """
        return self._collision

    @property
    def exit_state(self):
        """
        Returns the exit state flag:
            
            * :const:`EXIT_STATE_BACKSCATTERED`
            * :const:`EXIT_STATE_TRANSMITTED`
            * :const:`EXIT_STATE_ABSORBED`
        """
        return self._exit_state

    @property
    def interactions(self):
        """
        Returns two-dimensional array where each row corresponds to an 
        interaction of the particle. 
        The first three columns must be the x, y and z position (in m) of the 
        interaction, the fourth column, the energy at the position (in eV) and 
        the fifth, the type of collision. 
        The array can contain more columns.
        """
        return self._interactions

    def is_primary(self):
        """
        Returns whether this trajectory is from a primary particle.
        """
        return self._primary

    def is_secondary(self):
        """
        Returns whether this trajectory is from a secondary particle.
        """
        return not self._primary

class TrajectoryResult(_Result, Iterable, Sized):

    def __init__(self, trajectories=[]):
        self._trajectories = trajectories

    @classmethod
    def __loadhdf5__(cls, hdf5file, key):
        particles_ref = list(PARTICLES)
        particles_ref = dict(zip(map(int, particles_ref), particles_ref))

        collisions_ref = list(COLLISIONS)
        collisions_ref = dict(zip(map(int, collisions_ref), collisions_ref))

        trajectories = []

        size = float(len(hdf5file[key]))
        task = progress.start_task()
        task.status = 'Loading trajectories'

        for i, dataset in enumerate(hdf5file[key].itervalues()):
            task.progress = i / size

            primary = bool(dataset.attrs['primary'])
            particle = particles_ref[dataset.attrs['particle']]
            collision = collisions_ref[dataset.attrs['collision']]
            exit_state = int(dataset.attrs['exit_state'])
            interactions = dataset[:]

            trajectory = Trajectory(primary, particle, collision,
                                    exit_state, interactions)
            trajectories.append(trajectory)

        progress.stop_task(task)

        return cls(trajectories)

    def __savehdf5__(self, hdf5file, key):
        hdf5group = hdf5file.require_group(key)

        for index, trajectory in enumerate(self._trajectories):
            name = 'trajectory%s' % index
            dataset = hdf5group.create_dataset(name, data=trajectory.interactions)

            dataset.attrs['primary'] = trajectory.is_primary()
            dataset.attrs['particle'] = int(trajectory.particle)
            dataset.attrs['collision'] = int(trajectory.collision)
            dataset.attrs['exit_state'] = trajectory.exit_state

    def __len__(self):
        return len(self._trajectories)

    def __iter__(self):
        return iter(self._trajectories)

    def filter(self, is_primary=[True, False], particles=PARTICLES,
               collisions=COLLISIONS, exit_states=EXIT_STATES):
        """
        Filters the trajectories based on the specified criteria.
        Each criterion can a single value or a list of accepted values.
        Returns an iterator.
        
        :arg is_primary: whether to include primary particles. Possible values:
        
            * ``True``: only primary particles
            * ``False``: only secondary particles
            * ``[True, False]``: both primary and secondary particles
            
        :type is_primary: :class:`bool` or :class:`list`
        
        :arg particles: which particle(s) to include
        :type particles: :class:`_Particle` or :class:`list`
        
        :arg collisions: which collision(s) from which a trajectory initiated to 
            include. 
        :type collisions: :class:`_Collision` or :class:`list`
        
        :arg exit_states: which exit state(s) of a trajectory to include
        :type exit_states: :class:`int` or :class:`list`
        """
        if not hasattr(is_primary, '__contains__'): is_primary = [is_primary]
        if not hasattr(particles, '__contains__'): particles = [particles]
        if not hasattr(collisions, '__contains__'): collisions = [collisions]
        if not hasattr(exit_states, '__contains__'): exit_states = [exit_states]

        for trajectory in self:
            if trajectory._primary not in is_primary: continue
            if trajectory.particle not in particles: continue
            if trajectory.collision not in collisions: continue
            if trajectory.exit_state not in exit_states: continue

            yield trajectory

ResultManager.register('TrajectoryResult', TrajectoryResult)

class _ChannelsResult(_Result):

    def __init__(self, data):
        """
        Creates a new result to store a distribution.
        
        :arg data: numpy array containing 2 or 3 columns. The first column
            must be the mid-value of each bin, the second, the probability
            density and the third (optional), the uncertainty (3 sigma) on 
            the probability density.
        """
        _Result.__init__(self)

        if data.shape[1] < 2:
            raise ValueError, 'The data must contains at least two columns'
        if data.shape[1] == 2:
            data = np.append(data, np.zeros((data.shape[0], 1)), 1)

        self._data = data

    @classmethod
    def __loadhdf5__(cls, hdf5file, key):
        data = hdf5file[key]['data']
        return cls(data)

    def __savehdf5__(self, hdf5file, key):
        hdf5file.require_group(key).create_dataset('data', data=self._data)

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def get_data(self):
        return np.copy(self._data)

class BackscatteredElectronEnergyResult(_ChannelsResult):
    """
    Energy distribution of backscattered electrons.
    
    Data columns:
    
        1. Mid-energy of each bin (eV)
        2. probability density (counts/(eV.electron))
        3. uncertainty of the probability density (counts/(eV.electron))
    """
    pass

ResultManager.register('BackscatteredElectronEnergyResult', BackscatteredElectronEnergyResult)

class TransmittedElectronEnergyResult(_ChannelsResult):
    """
    Energy distribution of transmitted electrons.
    
    Data columns:
    
        1. Mid-energy of each bin (eV)
        2. probability density (counts/(eV.electron))
        3. uncertainty of the probability density (counts/(eV.electron))
    """
    pass

ResultManager.register('TransmittedElectronEnergyResult', TransmittedElectronEnergyResult)