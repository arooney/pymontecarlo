"""
Base classes for samples.
"""

# Standard library modules.
import abc
import math

# Third party modules.

# Local modules.
from pymontecarlo.options.material import VACUUM
from pymontecarlo.util.cbook import \
    DegreesAttribute, are_sequence_equal, unique
from pymontecarlo.options.option import Option, OptionBuilder

# Globals and constants variables.

class Sample(Option):
    """
    Base class for all sample representations.
    """

    TILT_TOLERANCE_deg = math.radians(1e-3) # 0.001 deg
    ROTATION_TOLERANCE_deg = math.radians(1e-3) # 0.001 deg

    def __init__(self, tilt_rad=0.0, rotation_rad=0.0):
        """
        Creates a new sample.
        
        :arg tilt_rad: tilt around the x-axis
        :type tilt_rad: :class:`float`
        
        :arg rotation_rad: rotation around the z-axis of the tilted sample
        :type rotation_rad: :class:`float`
        """
        super().__init__()

        self.tilt_rad = tilt_rad
        self.rotation_rad = rotation_rad

    def __eq__(self, other):
        return super().__eq__(other) and \
            math.isclose(self.tilt_deg, other.tilt_deg, abs_tol=self.TILT_TOLERANCE_deg) and \
            math.isclose(self.rotation_deg, other.rotation_deg, abs_tol=self.ROTATION_TOLERANCE_deg)

    def _cleanup_materials(self, *materials):
        materials = list(materials)

        if VACUUM in materials:
            materials.remove(VACUUM)

        return tuple(unique(materials))

    def create_datarow(self, **kwargs):
        datarow = super().create_datarow(**kwargs)
        datarow.add('sample tilt', self.tilt_rad, 0.0, 'rad')
        datarow.add('sample rotation', self.rotation_rad, 0.0, 'rad')
        return datarow

    @abc.abstractproperty
    def materials(self): #pragma: no cover
        """
        Returns a :class:`tuple` of all materials inside this geometry.
        :obj:`VACUUM` should not be included in the materials.
        """
        raise NotImplementedError

    tilt_deg = DegreesAttribute('tilt_rad')
    rotation_deg = DegreesAttribute('rotation_rad')

class SampleBuilder(OptionBuilder):

    def __init__(self):
        self.tilts_rad = set()
        self.rotations_rad = set()

    def __len__(self):
        tilts_rad, rotations_rad = self._get_combinations()
        return len(tilts_rad) * len(rotations_rad)

    def _get_combinations(self):
        tilts_rad = self.tilts_rad
        rotations_rad = self.rotations_rad

        if not tilts_rad:
            tilts_rad = [0.0]
        if not rotations_rad:
            rotations_rad = [0.0]

        return tilts_rad, rotations_rad

    def add_tilt_rad(self, tilt_rad):
        self.tilts_rad.add(tilt_rad)

    def add_tilt_deg(self, tilt_deg):
        self.add_tilt_deg(math.radians(tilt_deg))

    def add_rotation_rad(self, rotation_rad):
        self.rotations_rad.add(rotation_rad)

    def add_rotation_deg(self, rotation_deg):
        self.add_rotation_rad(math.radians(rotation_deg))

class Layer(object):

    THICKNESS_TOLERANCE_m = 1e-12 # 1 fm

    def __init__(self, material, thickness_m):
        """
        Layer of a sample.

        :arg material: material of the layer
        :type material: :class:`Material`

        :arg thickness_m: thickness of the layer in meters
        """
        self.material = material
        self.thickness_m = thickness_m

    def __repr__(self):
        return '<{0}(material={1}, thickness={2:g} m)>' \
            .format(self.__class__.__name__, self.material, self.thickness_m)

    def __eq__(self, other):
        return self.material == other.material and \
            math.isclose(self.thickness_m, other.thickness_m, abs_tol=self.THICKNESS_TOLERANCE_m)

class LayeredSample(Sample):

    def __init__(self, layers=None, tilt_rad=0.0, rotation_rad=0.0):
        super().__init__(tilt_rad, rotation_rad)

        if layers is None:
            layers = []
        self.layers = list(layers)

    def __eq__(self, other):
        return super().__eq__(other) and \
            are_sequence_equal(self.layers, other.layers)

    def add_layer(self, material, thickness_m):
        """
        Adds a layer to the geometry.
        The layer is added after the previous layers.

        :arg material: material of the layer
        :type material: :class:`Material`

        :arg thickness: thickness of the layer in meters
        """
        layer = Layer(material, thickness_m)
        self.layers.append(layer)
        return layer

    def create_datarow(self, **kwargs):
        datarow = super().create_datarow(**kwargs)
        for i, layer in enumerate(self.layers):
            prefix = "layer {0:d}'s ".format(i)
            datarow.update_with_prefix(prefix, layer.material.create_datarow(**kwargs))
            datarow.add(prefix + 'thickness', layer.thickness_m, 0.0, 'm')
        return datarow

    @property
    def materials(self):
        materials = [layer.material for layer in self.layers]
        return self._cleanup_materials(*materials)
