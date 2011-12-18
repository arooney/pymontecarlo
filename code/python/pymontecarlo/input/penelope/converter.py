#!/usr/bin/env python
"""
================================================================================
:mod:`converter` -- PENELOPE conversion from base options
================================================================================

.. module:: converter
   :synopsis: PENELOPE conversion from base options

.. inheritance-diagram:: pymontecarlo.input.penelope.converter

"""

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2011 Philippe T. Pinard"
__license__ = "GPL v3"

# Standard library modules.
import warnings

# Third party modules.

# Local modules.
from pymontecarlo.input.base.converter import \
    Converter as _Converter, ConversionWarning, ConversionException

from pymontecarlo.input.base.material import VACUUM
from pymontecarlo.input.penelope.material import Material, VACUUM as PenelopeVACUUM
from pymontecarlo.input.penelope.body import Body, Layer
from pymontecarlo.input.base.beam import GaussianBeam, PencilBeam
from pymontecarlo.input.base.geometry import \
    Substrate, MultiLayers, GrainBoundaries, Inclusion
from pymontecarlo.input.base.limit import TimeLimit, ShowersLimit, UncertaintyLimit
from pymontecarlo.input.base.detector import \
    (BackscatteredElectronAzimuthalAngularDetector,
     BackscatteredElectronEnergyDetector,
     BackscatteredElectronPolarAngularDetector,
     EnergyDepositedSpatialDetector,
     PhiRhoZDetector,
     PhotonAzimuthalAngularDetector,
     PhotonIntensityDetector,
     PhotonPolarAngularDetector,
     PhotonSpectrumDetector,
     TransmittedElectronAzimuthalAngularDetector,
     TransmittedElectronEnergyDetector,
     TransmittedElectronPolarAngularDetector)
from pymontecarlo.input.base.model import \
    (ELASTIC_CROSS_SECTION, INELASTIC_CROSS_SECTION, IONIZATION_CROSS_SECTION,
     BREMSSTRAHLUNG_EMISSION, PHOTON_SCATTERING_CROSS_SECTION,
     MASS_ABSORPTION_COEFFICIENT)

# Globals and constants variables.

class Converter(_Converter):
    BEAMS = [GaussianBeam]
    GEOMETRIES = [Substrate, MultiLayers, GrainBoundaries, Inclusion]
    DETECTORS = [BackscatteredElectronAzimuthalAngularDetector,
                 BackscatteredElectronEnergyDetector,
                 BackscatteredElectronPolarAngularDetector,
                 EnergyDepositedSpatialDetector,
                 PhiRhoZDetector,
                 PhotonAzimuthalAngularDetector,
                 PhotonIntensityDetector,
                 PhotonPolarAngularDetector,
                 PhotonSpectrumDetector,
                 TransmittedElectronAzimuthalAngularDetector,
                 TransmittedElectronEnergyDetector,
                 TransmittedElectronPolarAngularDetector]
    LIMITS = [TimeLimit, ShowersLimit, UncertaintyLimit]
    MODELS = {ELASTIC_CROSS_SECTION.type: [ELASTIC_CROSS_SECTION.elsepa2005],
              INELASTIC_CROSS_SECTION.type: [INELASTIC_CROSS_SECTION.sternheimer_liljequist1952],
              IONIZATION_CROSS_SECTION.type: [IONIZATION_CROSS_SECTION.bote_salvat2008],
              BREMSSTRAHLUNG_EMISSION.type: [BREMSSTRAHLUNG_EMISSION.seltzer_berger1985],
              PHOTON_SCATTERING_CROSS_SECTION.type: [PHOTON_SCATTERING_CROSS_SECTION.brusa1996],
              MASS_ABSORPTION_COEFFICIENT.type: [MASS_ABSORPTION_COEFFICIENT.llnl1989]}
    DEFAULT_MODELS = {ELASTIC_CROSS_SECTION.type: ELASTIC_CROSS_SECTION.elsepa2005,
                      INELASTIC_CROSS_SECTION.type: INELASTIC_CROSS_SECTION.sternheimer_liljequist1952,
                      IONIZATION_CROSS_SECTION.type: IONIZATION_CROSS_SECTION.bote_salvat2008,
                      BREMSSTRAHLUNG_EMISSION.type: BREMSSTRAHLUNG_EMISSION.seltzer_berger1985,
                      PHOTON_SCATTERING_CROSS_SECTION.type: PHOTON_SCATTERING_CROSS_SECTION.brusa1996,
                      MASS_ABSORPTION_COEFFICIENT.type: MASS_ABSORPTION_COEFFICIENT.llnl1989}


    def __init__(self, elastic_scattering=(0.0, 0.0),
                 cutoff_energy_inelastic=50.0,
                 cutoff_energy_bremsstrahlung=50.0):
        """
        Converter from base options to PENELOPE options.
        
        During the conversion, the materials are converted to :class:`PenelopeMaterial`. 
        For this, the specified elastic scattering and cutoff energies are used
        as the default values in the conversion.
        """
        _Converter.__init__(self)

        self._elastic_scattering = elastic_scattering
        self._cutoff_energy_inelastic = cutoff_energy_inelastic
        self._cutoff_energy_bremsstrahlung = cutoff_energy_bremsstrahlung

    def _convert_beam(self, options):
        try:
            _Converter._convert_beam(self, options)
        except ConversionException as ex:
            if isinstance(options.beam, PencilBeam):
                old = options.beam
                options.beam = GaussianBeam(old.energy, 0.0, old.origin,
                                            old.direction, old.aperture)

                message = "Pencil beam converted to Gaussian beam with 0 m diameter"
                warnings.warn(message, ConversionWarning)
            else:
                raise ex

    def _convert_geometry(self, options):
        _Converter._convert_geometry(self, options)

        geometry = options.geometry

        materials_lookup = self._create_penelope_materials(geometry.get_materials())

        if isinstance(geometry, Substrate):
            geometry._body = \
                self._create_penelope_body(geometry.body, materials_lookup)

        elif isinstance(geometry, Inclusion):
            geometry._substrate = \
                self._create_penelope_body(geometry.substrate_body, materials_lookup)
            geometry._inclusion = \
                self._create_penelope_body(geometry.inclusion_body, materials_lookup)

        elif isinstance(geometry, MultiLayers):
            if geometry.has_substrate():
                geometry._substrate = \
                    self._create_penelope_body(geometry.substrate_body, materials_lookup)

            newlayers = \
                self._create_penelope_layers(geometry.layers, materials_lookup)
            geometry.clear()
            geometry.layers.extend(newlayers)

        elif isinstance(geometry, GrainBoundaries):
            geometry._left = \
                self._create_penelope_body(geometry.left_body, materials_lookup)
            geometry._right = \
                self._create_penelope_body(geometry.right_body, materials_lookup)

            newlayers = \
                self._create_penelope_layers(geometry.layers, materials_lookup)
            geometry.clear()
            geometry.layers.extend(newlayers)
        else:
            raise ConversionException, "Cannot convert geometry"

    def _create_penelope_materials(self, oldmaterials):
        materials_lookup = {}

        for oldmaterial in oldmaterials:
            materials_lookup[oldmaterial] = self._create_penelope_material(oldmaterial)

        return materials_lookup

    def _create_penelope_material(self, old):
        if old is VACUUM:
            return PenelopeVACUUM

        return Material(old.name, old.composition, old.density,
                        old.absorption_energy_electron, old.absorption_energy_photon,
                        self._elastic_scattering,
                        self._cutoff_energy_inelastic, self._cutoff_energy_bremsstrahlung)

    def _create_penelope_body(self, old, materials_lookup):
        material = materials_lookup[old.material]
        return Body(material)

    def _create_penelope_layers(self, layers, materials_lookup):
        newlayers = []

        for layer in layers:
            material = materials_lookup[layer.material]

            # By default, the maximum step length in a layer is equal to 1/10 of 
            # the layer thickness
            maximum_step_length = layer.thickness / 10.0

            newlayers.append(Layer(material, layer.thickness, maximum_step_length))

        return newlayers


