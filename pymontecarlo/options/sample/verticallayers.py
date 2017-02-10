"""
Vertical layers sample
"""

# Standard library modules.

# Third party modules.

# Local modules.
from pymontecarlo.options.sample.base import LayeredSample

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

    def create_datarow(self):
        datarow = super().create_datarow()
        for name, value in self.left_material.create_datarow().items():
            datarow["left substrate's " + name] = value
        for name, value in self.right_material.create_datarow().items():
            datarow["right substrate's " + name] = value
        datarow["vertical layers' depth (m)"] = self.depth_m
        return datarow

    @property
    def materials(self):
        return self._cleanup_materials(self.left_material,
                                       self.right_material,
                                       *super().materials)

    @property
    def layers_xpositions_m(self):
        xpositions_m = []

        xmax_m = -sum(layer.thickness_m for layer in self.layers) / 2
        for layer in self.layers:
            xmin_m = xmax_m
            xmax_m = xmin_m + layer.thickness_m
            xpositions_m.append((xmin_m, xmax_m))

        return xpositions_m

#def _calculate_positions(self):
#        layers = np.array(self.geometry.layers, ndmin=1)
#        thicknesses = list(map(_THICKNESS_GETTER, layers))
#
#        positions = []
#        if thicknesses: # simple couple
#            middle = sum(thicknesses) / 2.0
#            for i in range(len(thicknesses)):
#                positions.append(sum(thicknesses[:i]) - middle)
#            positions.append(positions[-1] + thicknesses[-1])
#        else:
#            positions.append(0.0)
#
#        return positions
