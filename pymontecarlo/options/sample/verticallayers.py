"""
Vertical layers sample
"""

# Standard library modules.

# Third party modules.

# Local modules.
from .base import LayeredSample

# Globals and constants variables.

class VerticalLayerSample(LayeredSample):

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
        super().__init__(layers, tilt_rad, rotation_rad)

        self.left_material = left_material
        self.right_material = right_material

        self.depth_m = depth_m

    def __repr__(self):
        return '<{0:s}(left_material={1:s}, right_materials={2:s}, {3:d} layers)>' \
            .format(self.__class__.__name, self.left_substrate.material,
                    self.right_substrate.material, len(self.layers))

    def __eq__(self, other):
        return super().__eq__(other) and \
            self.left_material == other.left_material and \
            self.right_material == other.right_material and \
            self.depth_m == other.depth_m

    @property
    def materials(self):
        return self._cleanup_materials(self.left_material,
                                       self.right_material,
                                       *super().materials)