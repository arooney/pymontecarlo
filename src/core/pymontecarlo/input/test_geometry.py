#!/usr/bin/env python
""" """

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2011 Philippe T. Pinard"
__license__ = "GPL v3"

# Standard library modules.
import unittest
import logging

# Third party modules.

# Local modules.
from pymontecarlo.testcase import TestCase

from pymontecarlo.input.geometry import _Geometry, Substrate, Inclusion, Layer, MultiLayers, GrainBoundaries, ThinGrainBoundaries, Sphere
#    (_Geometry, Substrate, Inclusion, MultiLayers, GrainBoundaries, Sphere,
#     Cuboids2D, ThinGrainBoundaries)
from pymontecarlo.input.material import pure, VACUUM
from pymontecarlo.input.xmlmapper import mapper

# Globals and constants variables.

class GeometryMock(_Geometry):

    def __init__(self, tilt, rotation):
        _Geometry.__init__(self, tilt, rotation)

        mat = pure(29)
        self.materials = [mat]

    def get_materials(self):
        return set(self.materials)

mapper.register(GeometryMock, 'geometrymock')

class Test_Geometry(TestCase):

    def setUp(self):
        TestCase.setUp(self)

        self.g = GeometryMock(1.1, 2.2)

    def tearDown(self):
        TestCase.tearDown(self)

    def testskeleton(self):
        self.assertAlmostEqual(1.1, self.g.tilt_rad, 4)
        self.assertAlmostEqual(2.2, self.g.rotation_rad, 4)
        self.assertEqual(1, len(self.g.materials))

    def testget_materials(self):
        materials = self.g.get_materials()
        self.assertEqual(1, len(materials))

    def testto_xml(self):
        element = mapper.to_xml(self.g)

        self.assertAlmostEqual(1.1, float(element.get('tilt')), 4)
        self.assertAlmostEqual(2.2, float(element.get('rotation')), 4)

    def testfrom_xml(self):
        element = mapper.to_xml(self.g)
        g = mapper.from_xml(element)

        self.assertAlmostEqual(1.1, g.tilt_rad, 4)
        self.assertAlmostEqual(2.2, g.rotation_rad, 4)

class TestSubstrate(TestCase):

    def setUp(self):
        TestCase.setUp(self)

        self.g = Substrate(pure(29))

    def tearDown(self):
        TestCase.tearDown(self)

    def testskeleton(self):
        self.assertEqual('Copper', str(self.g.material))

    def testmaterial(self):
        self.g.material = pure(14)
        self.assertEqual('Silicon', str(self.g.material))

    def testget_materials(self):
        self.assertEqual(1, len(self.g.get_materials()))

    def testfrom_xml(self):
        self.g.tilt_rad = 1.1
        self.g.rotation_rad = 2.2
        self.g.material = [pure(29), pure(30)]
        element = mapper.to_xml(self.g)
        g = mapper.from_xml(element)

        self.assertEqual(2, len(g.material))
        self.assertEqual('Copper', str(g.material[0]))
        self.assertEqual('Zinc', str(g.material[1]))
        self.assertAlmostEqual(1.1, g.tilt_rad, 4)
        self.assertAlmostEqual(2.2, g.rotation_rad, 4)

    def testto_xml(self):
        self.g.material = [pure(29), pure(30)]
        element = mapper.to_xml(self.g)

        self.assertEqual(2, len(list(element.find('substrate'))))

class TestInclusion(TestCase):

    def setUp(self):
        TestCase.setUp(self)

        self.g = Inclusion(pure(29), pure(30), 123.456)

    def tearDown(self):
        TestCase.tearDown(self)

    def testskeleton(self):
        self.assertEqual('Copper', str(self.g.substrate_material))
        self.assertEqual('Zinc', str(self.g.inclusion_material))
        self.assertAlmostEqual(123.456, self.g.inclusion_diameter_m, 4)

    def testinclusion_diameter(self):
        self.assertAlmostEqual(123.456, self.g.inclusion_diameter_m, 4)

        self.assertRaises(ValueError, self.g.__setattr__, 'inclusion_diameter_m', -1)

    def testget_materials(self):
        self.assertEqual(2, len(self.g.get_materials()))

    def testfrom_xml(self):
        self.g.tilt_rad = 1.1
        self.g.rotation_rad = 2.2
        element = mapper.to_xml(self.g)
        g = mapper.from_xml(element)

        self.assertEqual('Copper', str(g.substrate_material))
        self.assertEqual('Zinc', str(g.inclusion_material))
        self.assertAlmostEqual(123.456, g.inclusion_diameter_m, 4)

        self.assertAlmostEqual(1.1, g.tilt_rad, 4)
        self.assertAlmostEqual(2.2, g.rotation_rad, 4)

    def testto_xml(self):
        element = mapper.to_xml(self.g)

        self.assertEqual(1, len(list(element.find('substrate'))))
        self.assertEqual(1, len(list(element.find('inclusion'))))

        self.assertAlmostEqual(123.456, float(element.get('diameter')), 4)
#
class TestMultiLayers(TestCase):

    def setUp(self):
        TestCase.setUp(self)

        self.g1 = MultiLayers(pure(29))
        self.g2 = MultiLayers(None) # No substrate
        self.g3 = MultiLayers(pure(29)) # Empty layer

        self.l1 = Layer(pure(30), 123.456)
        self.l2 = Layer(pure(31), 456.789)
        self.l3 = Layer(VACUUM, 456.123)

        self.g1.layers.append(self.l1)
        self.g1.layers.append(self.l2)

        self.g2.layers.append(self.l1)
        self.g2.layers.append(self.l2)

        self.g3.layers.append(self.l1)
        self.g3.layers.append(self.l2)
        self.g3.layers.append(self.l3)

    def tearDown(self):
        TestCase.tearDown(self)

    def testskeleton(self):
        # Multi-layers 1
        self.assertTrue(self.g1.has_substrate())
        self.assertEqual('Copper', str(self.g1.substrate_material))

        self.assertEqual(2, len(self.g1.layers))
        self.assertEqual('Zinc', str(self.g1.layers[0].material))
        self.assertEqual('Gallium', str(self.g1.layers[1].material))

        # Multi-layers 2
        self.assertFalse(self.g2.has_substrate())

        self.assertEqual(2, len(self.g2.layers))
        self.assertEqual('Zinc', str(self.g2.layers[0].material))
        self.assertEqual('Gallium', str(self.g2.layers[1].material))

        # Multi-layers 3
        self.assertTrue(self.g3.has_substrate())
        self.assertEqual('Copper', str(self.g3.substrate_material))

        self.assertEqual(3, len(self.g3.layers))
        self.assertEqual('Zinc', str(self.g3.layers[0].material))
        self.assertEqual('Gallium', str(self.g3.layers[1].material))
        self.assertEqual('Vacuum', str(self.g3.layers[2].material))

    def testsubstrate_material(self):
        self.g1.substrate_material = VACUUM
        self.assertFalse(self.g1.has_substrate())

    def testget_materials(self):
        self.assertEqual(3, len(self.g1.get_materials()))
        self.assertEqual(2, len(self.g2.get_materials()))
        self.assertEqual(3, len(self.g3.get_materials()))

    def testfrom_xml(self):
        # Multi-layers 1
        self.g1.tilt_rad = 1.1
        self.g1.rotation_rad = 2.2
        element = mapper.to_xml(self.g1)
        g1 = mapper.from_xml(element)

        self.assertTrue(g1.has_substrate())
        self.assertEqual('Copper', str(g1.substrate_material))

        self.assertEqual(2, len(g1.layers))
        self.assertEqual('Zinc', str(g1.layers[0].material))
        self.assertEqual('Gallium', str(g1.layers[1].material))

        self.assertAlmostEqual(1.1, g1.tilt_rad, 4)
        self.assertAlmostEqual(2.2, g1.rotation_rad, 4)

        # Multi-layers 2
        element = mapper.to_xml(self.g2)
        g2 = mapper.from_xml(element)

        self.assertFalse(g2.has_substrate())

        self.assertEqual(2, len(g2.layers))
        self.assertEqual('Zinc', str(g2.layers[0].material))
        self.assertEqual('Gallium', str(g2.layers[1].material))

        # Multi-layers 3
        element = mapper.to_xml(self.g3)
        g3 = mapper.from_xml(element)

        self.assertTrue(g3.has_substrate())
        self.assertEqual('Copper', str(g3.substrate_material))

        self.assertEqual(3, len(g3.layers))
        self.assertEqual('Zinc', str(g3.layers[0].material))
        self.assertEqual('Gallium', str(g3.layers[1].material))
        self.assertEqual('Vacuum', str(g3.layers[2].material))
#
    def testto_xml(self):
        # Multi-layers 1
        element = mapper.to_xml(self.g1)

        self.assertEqual(2, len(list(element.find('layers'))))
        self.assertEqual(1, len(list(element.find('substrate'))))

        # Multi-layers 2
        element = mapper.to_xml(self.g2)

        self.assertEqual(2, len(list(element.find('layers'))))
        self.assertEqual(1, len(list(element.find('substrate')))) # Vacuum

        # Multi-layers 3
        element = mapper.to_xml(self.g3)

        self.assertEqual(3, len(list(element.find('layers'))))
        self.assertEqual(1, len(list(element.find('substrate'))))

class TestGrainBoundaries(TestCase):

    def setUp(self):
        TestCase.setUp(self)

        self.g1 = GrainBoundaries(pure(29), pure(30))
        self.l1 = self.g1.add_layer(pure(31), 500.0)

        mat = pure(29)
        self.g2 = GrainBoundaries(mat, pure(30))
        self.l2 = self.g2.add_layer(mat, 100.0)
        self.l3 = self.g2.add_layer(pure(32), 200.0)

    def tearDown(self):
        TestCase.tearDown(self)

    def testskeleton(self):
        # Grain boundaries 1
        self.assertEqual('Copper', str(self.g1.left_material))
        self.assertEqual('Zinc', str(self.g1.right_material))

        self.assertEqual(1, len(self.g1.layers))
        self.assertEqual('Gallium', str(self.g1.layers[0].material))

        # Grain boundaries 2
        self.assertEqual('Copper', str(self.g2.left_material))
        self.assertEqual('Zinc', str(self.g2.right_material))

        self.assertEqual(2, len(self.g2.layers))
        self.assertEqual('Copper', str(self.g2.layers[0].material))
        self.assertEqual('Germanium', str(self.g2.layers[1].material))

    def testget_materials(self):
        self.assertEqual(3, len(self.g1.get_materials()))

    def testfrom_xml(self):
        # Grain boundaries 1
        self.g1.tilt_rad = 1.1
        self.g1.rotation_rad = 2.2
        element = mapper.to_xml(self.g1)
        g = mapper.from_xml(element)

        self.assertEqual('Copper', str(g.left_material))
        self.assertEqual('Zinc', str(g.right_material))

        self.assertEqual(1, len(g.layers))
        self.assertEqual('Gallium', str(g.layers[0].material))

        self.assertAlmostEqual(1.1, g.tilt_rad, 4)
        self.assertAlmostEqual(2.2, g.rotation_rad, 4)

        # Grain boundaries 2
        element = mapper.to_xml(self.g2)
        g = mapper.from_xml(element)

        self.assertEqual('Copper', str(g.left_material))
        self.assertEqual('Zinc', str(g.right_material))

        self.assertEqual(2, len(g.layers))
        self.assertEqual('Copper', str(g.layers[0].material))
        self.assertEqual('Germanium', str(g.layers[1].material))

        self.assertAlmostEqual(0.0, g.tilt_rad, 4)
        self.assertAlmostEqual(0.0, g.rotation_rad, 4)

    def testto_xml(self):
        # Grain boundaries 1
        element = mapper.to_xml(self.g1)

        self.assertEqual(1, len(list(element.find('layers'))))
        self.assertEqual(1, len(list(element.find('left'))))
        self.assertEqual(1, len(list(element.find('right'))))

        # Grain boundaries 2
        element = mapper.to_xml(self.g2)

        self.assertEqual(2, len(list(element.find('layers'))))
        self.assertEqual(1, len(list(element.find('left'))))
        self.assertEqual(1, len(list(element.find('right'))))

class TestThinGrainBoundaries(TestCase):

    def setUp(self):
        TestCase.setUp(self)

        self.g1 = ThinGrainBoundaries(pure(29), pure(30), 500.0)
        self.l1 = self.g1.add_layer(pure(31), 500.0)

        mat = pure(29)
        self.g2 = ThinGrainBoundaries(mat, pure(30), 400.0)
        self.l2 = self.g2.add_layer(mat, 100.0)
        self.l3 = self.g2.add_layer(pure(32), 200.0)

    def tearDown(self):
        TestCase.tearDown(self)

    def testskeleton(self):
        # Grain boundaries 1
        self.assertEqual('Copper', str(self.g1.left_material))
        self.assertEqual('Zinc', str(self.g1.right_material))

        self.assertEqual(1, len(self.g1.layers))
        self.assertEqual('Gallium', str(self.g1.layers[0].material))

        self.assertAlmostEqual(500.0, self.g1.thickness_m, 4)

        # Grain boundaries 2
        self.assertEqual('Copper', str(self.g2.left_material))
        self.assertEqual('Zinc', str(self.g2.right_material))

        self.assertEqual(2, len(self.g2.layers))
        self.assertEqual('Copper', str(self.g2.layers[0].material))
        self.assertEqual('Germanium', str(self.g2.layers[1].material))

        self.assertAlmostEqual(400.0, self.g2.thickness_m, 4)

    def testget_materials(self):
        self.assertEqual(3, len(self.g1.get_materials()))

    def testfrom_xml(self):
        # Grain boundaries 1
        self.g1.tilt_rad = 1.1
        self.g1.rotation_rad = 2.2
        element = mapper.to_xml(self.g1)
        g = mapper.from_xml(element)

        self.assertEqual('Copper', str(g.left_material))
        self.assertEqual('Zinc', str(g.right_material))

        self.assertEqual(1, len(g.layers))
        self.assertEqual('Gallium', str(g.layers[0].material))

        self.assertAlmostEqual(1.1, g.tilt_rad, 4)
        self.assertAlmostEqual(2.2, g.rotation_rad, 4)

        self.assertAlmostEqual(500.0, g.thickness_m, 4)

        # Grain boundaries 2
        element = mapper.to_xml(self.g2)
        g = mapper.from_xml(element)

        self.assertEqual('Copper', str(g.left_material))
        self.assertEqual('Zinc', str(g.right_material))

        self.assertEqual(2, len(g.layers))
        self.assertEqual('Copper', str(g.layers[0].material))
        self.assertEqual('Germanium', str(g.layers[1].material))

        self.assertAlmostEqual(0.0, g.tilt_rad, 4)
        self.assertAlmostEqual(0.0, g.rotation_rad, 4)

        self.assertAlmostEqual(400.0, g.thickness_m, 4)

    def testto_xml(self):
        # Grain boundaries 1
        element = mapper.to_xml(self.g1)

        self.assertEqual(1, len(list(element.find('layers'))))
        self.assertEqual(1, len(list(element.find('left'))))
        self.assertEqual(1, len(list(element.find('right'))))

        self.assertAlmostEqual(500, float(element.get('thickness')), 4)

        # Grain boundaries 2
        element = mapper.to_xml(self.g2)

        self.assertEqual(2, len(list(element.find('layers'))))
        self.assertEqual(1, len(list(element.find('left'))))
        self.assertEqual(1, len(list(element.find('right'))))

        self.assertAlmostEqual(400, float(element.get('thickness')), 4)

class TestSphere(TestCase):

    def setUp(self):
        TestCase.setUp(self)

        self.g = Sphere(pure(29), 123.456)

    def tearDown(self):
        TestCase.tearDown(self)

    def testskeleton(self):
        self.assertEqual('Copper', str(self.g.material))
        self.assertAlmostEqual(123.456, self.g.diameter_m, 4)

    def testdiameter_m(self):
        self.assertAlmostEqual(123.456, self.g.diameter_m, 4)

        self.assertRaises(ValueError, self.g.__setattr__, 'diameter_m', -1)

    def testget_materials(self):
        self.assertEqual(1, len(self.g.get_materials()))

    def testfrom_xml(self):
        self.g.tilt_rad = 1.1
        self.g.rotation_rad = 2.2
        element = mapper.to_xml(self.g)
        g = mapper.from_xml(element)

        self.assertEqual('Copper', str(g.material))
        self.assertAlmostEqual(123.456, g.diameter_m, 4)

        self.assertAlmostEqual(1.1, g.tilt_rad, 4)
        self.assertAlmostEqual(2.2, g.rotation_rad, 4)

    def testto_xml(self):
        element = mapper.to_xml(self.g)

        self.assertEqual(1, len(list(element.find('body'))))

        self.assertAlmostEqual(123.456, float(element.get('diameter')), 4)
##
###class TestCuboids2D(TestCase):
###
###    def setUp(self):
###        TestCase.setUp(self)
###
###        self.g = Cuboids2D(3, 3, 10, 10)
###        self.g.material[0, 0] = pure(29)
###        self.g.material[-1, -1] = pure(79)
###
###    def tearDown(self):
###        TestCase.tearDown(self)
###
###    def testskeleton(self):
###        self.assertEqual('Copper', str(self.g.material[0, 0]))
###        self.assertEqual('Gold', str(self.g.material[-1, -1]))
###        self.assertEqual('Vacuum', str(self.g.material[1, 1]))
###
###        self.assertEqual(3, self.g.nx)
###        self.assertEqual(3, self.g.ny)
###
###        self.assertAlmostEqual(10.0, self.g.xsize_m, 4)
###        self.assertAlmostEqual(10.0, self.g.ysize_m, 4)
###
###    def testfrom_xml(self):
###        self.g.tilt_rad = 1.1
###        self.g.rotation_rad = 2.2
###        element = self.g.to_xml()
###        g = Cuboids2D.from_xml(element)
###
###        self.assertEqual('Copper', str(self.g.material[0, 0]))
###        self.assertEqual('Gold', str(self.g.material[-1, -1]))
###        self.assertEqual('Vacuum', str(self.g.material[1, 1]))
###
###        self.assertAlmostEqual(10.0, self.g.xsize_m, 4)
###        self.assertAlmostEqual(10.0, self.g.ysize_m, 4)
###
###        self.assertAlmostEqual(1.1, g.tilt_rad, 4)
###        self.assertAlmostEqual(2.2, g.rotation_rad, 4)
###
###    def testbody(self):
###        self.assertEqual('Copper', str(self.g.body[0, 0].material))
###        self.assertEqual('Gold', str(self.g.body[-1, -1].material))
###        self.assertEqual('Vacuum', str(self.g.body[1, 1].material))
###
###        self.assertRaises(IndexError, self.g.body.__getitem__, (2, 2))
###
###    def testmaterial(self):
###        self.assertEqual('Copper', str(self.g.material[0, 0]))
###        self.assertEqual('Gold', str(self.g.material[-1, -1]))
###        self.assertEqual('Vacuum', str(self.g.material[1, 1]))
###
###        self.assertRaises(IndexError, self.g.material.__getitem__, (2, 2))
###
###    def testget_bodies(self):
###        self.assertEqual(9, len(self.g.get_bodies()))
###
###    def testget_dimensions(self):
###        dim = self.g.get_dimensions(self.g.body[0, 0])
###        self.assertAlmostEqual(-5.0, dim.xmin_m, 4)
###        self.assertAlmostEqual(5.0, dim.xmax_m, 4)
###        self.assertAlmostEqual(-5.0, dim.ymin_m, 4)
###        self.assertAlmostEqual(5.0, dim.ymax_m, 4)
###        self.assertEqual(float('-inf'), dim.zmin_m)
###        self.assertAlmostEqual(0.0, dim.zmax_m, 4)
###
###        dim = self.g.get_dimensions(self.g.body[-1, 0])
###        self.assertAlmostEqual(-15.0, dim.xmin_m, 4)
###        self.assertAlmostEqual(-5.0, dim.xmax_m, 4)
###        self.assertAlmostEqual(-5.0, dim.ymin_m, 4)
###        self.assertAlmostEqual(5.0, dim.ymax_m, 4)
###        self.assertEqual(float('-inf'), dim.zmin_m)
###        self.assertAlmostEqual(0.0, dim.zmax_m, 4)
###
###        dim = self.g.get_dimensions(self.g.body[1, 0])
###        self.assertAlmostEqual(5.0, dim.xmin_m, 4)
###        self.assertAlmostEqual(15.0, dim.xmax_m, 4)
###        self.assertAlmostEqual(-5.0, dim.ymin_m, 4)
###        self.assertAlmostEqual(5.0, dim.ymax_m, 4)
###        self.assertEqual(float('-inf'), dim.zmin_m)
###        self.assertAlmostEqual(0.0, dim.zmax_m, 4)
###
###        dim = self.g.get_dimensions(self.g.body[0, -1])
###        self.assertAlmostEqual(-5.0, dim.xmin_m, 4)
###        self.assertAlmostEqual(5.0, dim.xmax_m, 4)
###        self.assertAlmostEqual(-15.0, dim.ymin_m, 4)
###        self.assertAlmostEqual(-5.0, dim.ymax_m, 4)
###        self.assertEqual(float('-inf'), dim.zmin_m)
###        self.assertAlmostEqual(0.0, dim.zmax_m, 4)
###
###        dim = self.g.get_dimensions(self.g.body[0, 1])
###        self.assertAlmostEqual(-5.0, dim.xmin_m, 4)
###        self.assertAlmostEqual(5.0, dim.xmax_m, 4)
###        self.assertAlmostEqual(5.0, dim.ymin_m, 4)
###        self.assertAlmostEqual(15.0, dim.ymax_m, 4)
###        self.assertEqual(float('-inf'), dim.zmin_m)
###        self.assertAlmostEqual(0.0, dim.zmax_m, 4)
###
###    def testto_xml(self):
###        element = self.g.to_xml()
###
###        self.assertEqual(2, len(list(element.find('materials'))))
###        self.assertEqual(9, len(list(element.find('bodies'))))
###        self.assertEqual(9, len(list(element.find('positions'))))
###
###        self.assertEqual(3, int(element.get('nx')))
###        self.assertEqual(3, int(element.get('ny')))
###        self.assertAlmostEqual(10.0, float(element.get('xsize')), 4)
###        self.assertAlmostEqual(10.0, float(element.get('ysize')), 4)

if __name__ == '__main__': #pragma: no cover
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()
