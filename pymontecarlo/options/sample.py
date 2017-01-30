"""
Sample geometries.
"""

__all__ = ['VerticalLayers',
           'Inclusion',
           'HorizontalLayers',
           'Sphere',
           'Substrate']

# Standard library modules.
import abc
import math

# Third party modules.

# Local modules.
from pymontecarlo.options.material import VACUUM
from pymontecarlo.util.cbook import MultiplierAttribute

# Globals and constants variables.

class _Sample(metaclass=abc.ABCMeta):
    """
    Base class for all sample representations.
    """

    def __init__(self, tilt_rad=0.0, rotation_rad=0.0):
        """
        Creates a new sample.
        
        :arg tilt_rad: tilt around the x-axis
        :type tilt_rad: :class:`float`
        
        :arg rotation_rad: rotation around the z-axis of the tilted sample
        :type rotation_rad: :class:`float`
        """
        self.tilt_rad = tilt_rad
        self.rotation_rad = rotation_rad

    @abc.abstractmethod
    def get_materials(self):
        """
        Returns a :class:`tuple` of all materials inside this geometry.
        """
        raise NotImplementedError

    tilt_deg = MultiplierAttribute('tilt_rad', 180.0 / math.pi)
    rotation_deg = MultiplierAttribute('rotation_rad', 180.0 / math.pi)

class Substrate(_Sample):

    def __init__(self, material, tilt_rad=0.0, rotation_rad=0.0):
        """
        Creates a substrate sample. 
        At tilt of 0.0\u00b0, the sample is entirely made of the specified 
        material below ``z = 0``.
        """
        super().__init__(tilt_rad, rotation_rad)
        self.material = material

    def __repr__(self):
        return '<{0:s}(material={1:s})>' \
            .format(self.__class__.__name__, self.material)

    def get_materials(self):
        return (self.material,)

class Inclusion(_Sample):

    def __init__(self, substrate_material,
                 inclusion_material, inclusion_diameter_m,
                 tilt_rad=0.0, rotation_rad=0.0):
        """
        Creates an inclusion sample.
        The sample consists of a hemisphere inclusion inside a substrate.
        """
        super().__init__(tilt_rad, rotation_rad)

        self.substrate_material = substrate_material
        self.inclusion_material = inclusion_material
        self.inclusion_diameter_m = inclusion_diameter_m

    def __repr__(self):
        return '<{0:s}(substrate_material={1:s}, inclusion_material={2:s}, inclusion_diameter={3:g} m)>' \
            .format(self.__class__.__name__, self.substrate.material,
                    self.inclusion.material, self.inclusion.diameter_m)

    def get_materials(self):
        return (self.substrate_material, self.inclusion_material)

class Layer(object):

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
        return '<{0:s}(material={1:s}, thickness={2:g} m)>' \
            .format(self.__class__.__name__, self.material, self.thickness_m)

class HorizontalLayers(_Sample):

    def __init__(self, substrate_material=None, layers=None,
                 tilt_rad=0.0, rotation_rad=0.0):
        """
        Creates a multi-layers geometry.
        The layers are assumed to be in the x-y plane (normal parallel to z) at
        tilt of 0.0\u00b0.
        The first layer starts at ``z = 0`` and extends towards the negative z
        axis.

        :arg substrate_material: material of the substrate.
            If ``None``, the geometry does not have a substrate, only layers
        :arg layers: :class:`list` of :class:`.Layer`
        """
        super().__init__(tilt_rad, rotation_rad)

        if substrate_material is None:
            substrate_material = VACUUM
        self.substrate_material = substrate_material

        if layers is None:
            layers = []
        self.layers = list(layers)

    def __repr__(self):
        if self.has_substrate():
            return '<{0:s}(substrate_material={1:s}, {2:d} layers)>' \
                .format(self.__class__.__name, self.substrate.material,
                        len(self.layers))
        else:
            return '<{0:s}(No substrate, {1:d} layers)>' \
                .format(self.__class__.__name, len(self.layers))

    def has_substrate(self):
        """
        Returns ``True`` if a substrate material has been defined.
        """
        return self.substrate_material is not VACUUM

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

    def get_materials(self):
        materials = [self.substrate_material]
        materials += [layer.material for layer in self.layers]
        return tuple(materials)

class VerticalLayers(_Sample):

    def __init__(self, left_material, right_material, layers=None,
                 depth_m=float('inf'), tilt_rad=0.0, rotation_rad=0.0):
        """
        Creates a grain boundaries sample.
        It consists of 0 or many layers in the y-z plane (normal parallel to x)
        simulating interfaces between different materials.
        If no layer is defined, the geometry is a couple.

        :arg left_material: material on the left side
        :arg right_material: material on the right side
        :arg layers: :class:`list` of :class:`.Layer`
        """
        super().__init__(tilt_rad, rotation_rad)

        self.left_material = left_material
        self.right_material = right_material

        if layers is None:
            layers = []
        self.layers = list(layers)

        self.depth_m = depth_m

    def __repr__(self):
        return '<{0:s}(left_material={1:s}, right_materials={2:s}, {3:d} layers)>' \
            .format(self.__class__.__name, self.left_substrate.material,
                    self.right_substrate.material, len(self.layers))

    def add_layer(self, material, thickness):
        """
        Adds a layer to the geometry.
        The layer is added after the previous layers.

        :arg material: material of the layer
        :type material: :class:`Material`

        :arg thickness: thickness of the layer in meters
        """
        layer = Layer(material, thickness)
        self.layers.append(layer)
        return layer

    def get_materials(self):
        materials = [self.left_material, self.right_material]
        materials += [layer.material for layer in self.layers]
        return tuple(materials)

class Sphere(_Sample):

    def __init__(self, material, diameter_m, tilt_rad=0.0, rotation_rad=0.0):
        """
        Creates a geometry consisting of a sphere.
        The sphere is entirely located below the ``z=0`` plane.

        :arg material: material
        :arg diameter_m: diameter (in meters)
        """
        super().__init__(tilt_rad, rotation_rad)
        self.material = material
        self.diameter_m = diameter_m

    def __repr__(self):
        return '<{0:s}(material={1:s}, diameter={2:g} m)>' \
                    .format(self.__class__.__name, self.body.material,
                            self.diameter_m)

    def get_materials(self):
        return (self.material,)

