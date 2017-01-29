""""""

# Standard library modules.
import string
from collections import defaultdict
from fractions import gcd
import itertools

# Third party modules.
from pyparsing import Word, Group, Optional, OneOrMore

# Local modules.
import pyxray

# Globals and constants variables.

_symbol = Word(string.ascii_uppercase, string.ascii_lowercase)
_digit = Word(string.digits + ".")
_elementRef = Group(_symbol + Optional(_digit, default="1"))
CHEMICAL_FORMULA_PARSER = OneOrMore(_elementRef)

def composition_from_formula(formula):
    # Parse chemical formula
    formulaData = CHEMICAL_FORMULA_PARSER.parseString(formula)

    zs = []
    atomicfractions = []
    for symbol, atomicfraction in formulaData:
        zs.append(pyxray.element_atomic_number(symbol))
        atomicfractions.append(float(atomicfraction))

    # Calculate total atomic mass
    totalatomicmass = 0.0
    for z, atomicfraction in zip(zs, atomicfractions):
        atomicmass = pyxray.element_atomic_weight(z)
        totalatomicmass += atomicfraction * atomicmass

    # Create composition
    composition = defaultdict(float)

    for z, atomicfraction in zip(zs, atomicfractions):
        atomicmass = pyxray.element_atomic_weight(z)
        weightfraction = atomicfraction * atomicmass / totalatomicmass
        composition[z] += weightfraction

    return composition

def calculate_composition_atomic(composition):
    """
    Returns a composition :class:`dict` where the values are atomic fractions.

    :arg composition: composition in weight fraction.
        The composition is specified by a dictionary.
        The key are atomic numbers and the values weight fractions.
        No wildcard are accepted.
    :type composition: :class:`dict`
    """
    composition2 = {}

    for z, weightfraction in composition.items():
        composition2[z] = weightfraction / pyxray.element_atomic_weight(z)

    totalfraction = sum(composition2.values())

    for z, fraction in composition2.items():
        composition2[z] = fraction / totalfraction

    return defaultdict(float, composition2)

def calculate_density_kg_per_m3(composition):
    """
    Returns an estimate density from the composition using the pure element
    density and this equation.

    .. math::

       \\frac{1}{\\rho} = \\sum{\\frac{1}{\\rho_i}}

    :arg composition: composition in weight fraction.
        The composition is specified by a dictionary.
        The key are atomic numbers and the values weight fractions.
        No wildcard are accepted.
    :type composition: :class:`dict`
    """
    density = 0.0

    for z, fraction in composition.items():
        density += fraction / pyxray.element_mass_density_kg_per_m3(z)

    return 1.0 / density

def generate_name(composition):
    """
    Generates a name from the composition.
    The name is generated on the basis of a classical chemical formula.

    :arg composition: composition in weight fraction.
        The composition is specified by a dictionary.
        The key are atomic numbers and the values weight fractions.
        No wildcard are accepted.
    :type composition: :class:`dict`
    """
    composition_atomic = calculate_composition_atomic(composition)

    symbols = []
    fractions = []
    for z in sorted(composition_atomic.keys(), reverse=True):
        symbols.append(pyxray.element_symbol(z))
        fractions.append(int(composition_atomic[z] * 100.0))

    # Find gcd of the fractions
    smallest_gcd = 100
    if len(fractions) >= 2:
        gcds = []
        for a, b in itertools.combinations(fractions, 2):
            gcds.append(gcd(a, b))
        smallest_gcd = min(gcds)

    if smallest_gcd == 0.0:
        smallest_gcd = 100.0

    # Write formula
    name = ''
    for symbol, fraction in zip(symbols, fractions):
        fraction /= smallest_gcd
        if fraction == 0:
            continue
        elif fraction == 1:
            name += "%s" % symbol
        else:
            name += '%s%i' % (symbol, fraction)

    return name