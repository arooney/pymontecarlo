#!/usr/bin/env python
"""
================================================================================
:mod:`material` -- Material definition
================================================================================

.. module:: material
   :synopsis: Material definition

.. inheritance-diagram:: material

"""

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2011 Philippe T. Pinard"
__license__ = "GPL v3"

# Standard library modules.
from xml.etree.ElementTree import Element
from collections import defaultdict

# Third party modules.
from pyparsing import Word, Group, Optional, OneOrMore

# Local modules.
from pymontecarlo.util.xmlutil import objectxml
import pymontecarlo.util.element_properties as ep

# Globals and constants variables.

def composition_from_formula(formula):
    """
    Returns a list of tuples (atomic number, weight fraction) from the
    specified chemical formula.
    
    :arg formula: chemical formula (e.g. ``'AlB2Zr5'``).
    """
    # Parse chemical formula
    caps = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    lowers = caps.lower()
    digits = "0124356789"

    element = Word(caps, lowers)
    integer = Word(digits)
    elementRef = Group(element + Optional(integer, default="1"))
    chemicalFormula = OneOrMore(elementRef)

    formulaData = chemicalFormula.parseString(formula)

    zs = []
    atomicfractions = []
    for symbol, atomicfraction in formulaData:
        zs.append(ep.atomic_number(symbol=symbol))
        atomicfractions.append(float(atomicfraction))

    # Calculate total atomic mass
    totalatomicmass = 0.0
    for z, atomicfraction in zip(zs, atomicfractions):
        atomicmass = ep.atomic_mass(z)
        totalatomicmass += atomicfraction * atomicmass

    # Create composition
    composition = defaultdict(float)

    for z, atomicfraction in zip(zs, atomicfractions):
        atomicmass = ep.atomic_mass(z)
        weightfraction = atomicfraction * atomicmass / totalatomicmass

        composition[z] += weightfraction

    return composition

def pure(z, absorption_energy_electron=50.0, absorption_energy_photon=50.0):
    """
    Returns the material for the specified pure element.
    
    :arg z: atomic number
    :type z: :class:`int`
    
    :arg absorption_energy_electron: absorption energy of the electrons in
            this material.
    :type absorption_energy_electron: :class:`float`
    
    :arg absorption_energy_photon: absorption energy of the photons in
        this material.
    :type absorption_energy_photon: :class:`float`
    """
    name = ep.name(z)
    composition = {z: '?'}

    return Material(name, composition, None,
                    absorption_energy_electron, absorption_energy_photon)

class Material(objectxml):

    def __init__(self, name, composition, density=None,
                 absorption_energy_electron=50.0, absorption_energy_photon=50.0):
        """
        Creates a new material.
        
        :arg name: name of the material
        :type name: :class:`str`
        
        :arg composition: composition in weight fraction. 
            The composition is specified by a dictionary.
            The key can either be the atomic number or the symbol of the element.
            It will automatically be converted to the atomic number.
            The value is the weight fraction between ]0.0, 1.0] or ``?`` 
            indicating that the weight fraction is unknown and shall be 
            automatically calculated to make the total weight fraction equal 
            to 1.0. 
        :type composition: :class:`dict`
        
        :arg density: material's density in kg/m3.
            If the density is ``None`` or less than 0 (default), it will be 
            automatically calculated based on the density of the elements and 
            their weight fraction.
        :type density: :class:`float`
        
        :arg absorption_energy_electron: absorption energy of the electrons in
            this material.
        :type absorption_energy_electron: :class:`float`
        
        :arg absorption_energy_photon: absorption energy of the photons in
            this material.
        :type absorption_energy_photon: :class:`float`
        """
        self.name = name
        self.composition = composition
        self.density = density

        self.absorption_energy_electron = absorption_energy_electron
        self.absorption_energy_photon = absorption_energy_photon

    def __repr__(self):
        return '<Material(name=%s, composition=%s, density=%s kg/m3, abs_electron=%s eV, abs_photon=%s eV)>' % \
            (self._name, self.composition, self.density,
             self.absorption_energy_electron, self.absorption_energy_photon)

    def __str__(self):
        return self._name

    @classmethod
    def __loadxml__(cls, element, *args, **kwargs):
        name = element.get('name')

        composition = {}
        for child in iter(element.find('composition')):
            composition[int(child.get('z'))] = float(child.get('weightFraction'))

        density = float(element.get('density'))

        abs_electron = float(element.get('absorptionEnergyElectron'))
        abs_photon = float(element.get('absorptionEnergyPhoton'))

        return cls(name, composition, density, abs_electron, abs_photon)

    def __savexml__(self, element, *args, **kwargs):
        element.set('name', self._name)

        child = Element('composition')
        for z, fraction in self.composition.iteritems():
            child.append(Element('element', {'z': str(z), 'weightFraction': str(fraction)}))
        element.append(child)

        element.set('density', str(self.density))

        element.set('absorptionEnergyElectron', str(self.absorption_energy_electron))
        element.set('absorptionEnergyPhoton', str(self.absorption_energy_photon))

    def __calculate_composition(self, composition):
        composition2 = {}
        for element, fraction in composition.iteritems():
            # Replace symbol by atomic number
            if isinstance(element, basestring): # symbol
                element = ep.atomic_number(symbol=element)

            # Atomic number check
            if element <= 0 or element > 96:
                raise ValueError, "Atomic number (%i) must be between [1, 96]" % element

            # Fraction check
            if fraction != '?':
                if fraction <= 0 or fraction > 1.0:
                    raise ValueError, "Fraction (%s) must be between ]0.0, 1.0]" % fraction

            composition2[element] = fraction

        # Replace wildcard
        totalfraction = 0.0
        countwildcard = 0
        for fraction in composition2.values():
            if fraction == '?':
                countwildcard += 1
            else:
                totalfraction += fraction

        if countwildcard > 0:
            if totalfraction < 1.0:
                wildcardfraction = (1.0 - totalfraction) / float(countwildcard)
            else:
                wildcardfraction = 0.0

        composition3 = {}
        for z, fraction in composition2.iteritems():
            if fraction == '?':
                fraction = wildcardfraction
            composition3[z] = fraction

        # Check total fraction
        totalfraction = sum(composition3.values())
        if (totalfraction - 1.0) > 1e-6:
            raise ValueError, "The total weight fraction (%s) should be 1.0." % totalfraction

        return composition3

    def __calculate_density(self):
        density = 0.0

        for z, fraction in self.composition.iteritems():
            density += ep.mass_density(z) * fraction

        return density

    @property
    def name(self):
        """
        Name of the material.
        """
        return self._name

    @name.setter
    def name(self, name):
        self._name = name

    @property
    def composition(self):
        """
        Composition of this material.
        The composition is specified by a list of tuple.
        The first element of each tuple is the atomic number and the second
        is the weight fraction.
        """
        return dict(self._composition) # copy

    @composition.setter
    def composition(self, composition):
        self._composition = self.__calculate_composition(composition)

    @property
    def density(self):
        """
        Density of this material in kg/m3.
        """
        if self.has_density_defined():
            return self._density
        else:
            return self.__calculate_density()

    @density.setter
    def density(self, density):
        self._density = density

    @density.deleter
    def density(self):
        self._density = None

    def has_density_defined(self):
        """
        Returns ``True`` if the density was specified by the user, ``False`` if
        it is automatically calculated from the composition.
        """
        return self._density is not None and self._density >= 0.0

    @property
    def absorption_energy_electron(self):
        """
        Absorption energy of the electrons in this material.
        """
        return self._absorption_energy_electron

    @absorption_energy_electron.setter
    def absorption_energy_electron(self, energy):
        if energy < 0.0:
            raise ValueError, "Absorption energy (%s) must be greater or equal to 0.0" \
                    % energy
        self._absorption_energy_electron = energy

    @property
    def absorption_energy_photon(self):
        """
        Absorption energy of the photons in this material.
        """
        return self._absorption_energy_photon

    @absorption_energy_photon.setter
    def absorption_energy_photon(self, energy):
        if energy < 0.0:
            raise ValueError, "Absorption energy (%s) must be greater or equal to 0.0" \
                    % energy
        self._absorption_energy_photon = energy

class _Vacuum(Material):
    def __init__(self):
        Material.__init__(self, "Vacuum", {}, 0.0, 0.0, 0.0)
        self._index = 0

VACUUM = _Vacuum()