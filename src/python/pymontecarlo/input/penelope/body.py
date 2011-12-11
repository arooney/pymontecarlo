#!/usr/bin/env python
"""
================================================================================
:mod:`body` -- PENELOPE body for geometry
================================================================================

.. module:: body
   :synopsis: PENELOPE body for geometry

.. inheritance-diagram:: body

"""

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2011 Philippe T. Pinard"
__license__ = "GPL v3"

# Standard library modules.
from xml.etree.ElementTree import Element

# Third party modules.

# Local modules.
from pymontecarlo.input.base.body import Body as _Body, Layer as _Layer
from pymontecarlo.input.penelope.interactionforcing import InteractionForcing

# Globals and constants variables.

class Body(_Body):
    def __init__(self, material, maximum_step_length=1e20):
        _Body.__init__(self, material)

        self._interaction_forcings = set()
        self.maximum_step_length = maximum_step_length

    def __repr__(self):
        return '<Body(material=%s, %i interaction forcing(s), dsmax=%s m)>' % \
            (str(self.material), len(self.interaction_forcings), self.maximum_step_length)

    @classmethod
    def __loadxml__(cls, element, material=None, *args, **kwargs):
        body = _Body.__loadxml__(element, material, *args, **kwargs)
        maximum_step_length = float(element.get('maximumStepLength'))

        obj = cls(body.material, maximum_step_length)

        children = list(element.find("interactionForcings"))
        for child in children:
            obj.interaction_forcings.add(InteractionForcing.from_xml(child))

        return obj

    def __savexml__(self, element, *args, **kwargs):
        _Body.__savexml__(self, element, *args, **kwargs)

        child = Element("interactionForcings")
        for intforce in self.interaction_forcings:
            child.append(intforce.to_xml())
        element.append(child)

        element.set('maximumStepLength', str(self.maximum_step_length))

    @property
    def interaction_forcings(self):
        """
        Set of interaction forcings.
        Use :meth:`add` to add an interaction forcing to this body.
        """
        return self._interaction_forcings

    @property
    def maximum_step_length(self):
        """
        Maximum length of an electron trajectory in this body (in meters).
        """
        return self._maximum_step_length

    @maximum_step_length.setter
    def maximum_step_length(self, length):
        if length < 0 or length > 1e20:
            raise ValueError, "Length (%s) must be between [0, 1e20]." % length

        self._maximum_step_length = length

class Layer(Body, _Layer):
    def __init__(self, material, thickness, maximum_step_length=None):
        _Layer.__init__(self, material, thickness)

        if maximum_step_length is None:
            maximum_step_length = thickness / 10.0
        Body.__init__(self, material, maximum_step_length)

    @classmethod
    def __loadxml__(cls, element, material=None, thickness=None, *args, **kwargs):
        layer = _Layer.__loadxml__(element, material, thickness, *args, **kwargs)
        body = Body.__loadxml__(element, material, *args, **kwargs)

        return cls(layer.material, layer.thickness, body.maximum_step_length)

    def __savexml__(self, element, *args, **kwargs):
        Body.__savexml__(self, element, *args, **kwargs)
        _Layer.__savexml__(self, element, *args, **kwargs)
