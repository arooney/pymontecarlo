"""
Ionization cross section models.
"""

# Standard library modules.

# Third party modules.

# Local modules.
from pymontecarlo.options.model.base import Model

# Globals and constants variables.

class IonizationCrossSectionModel(Model):

    @property
    def category(self):
        return 'ionization cross section'

GAUVIN = IonizationCrossSectionModel('Gauvin')
POUCHOU1996 = IonizationCrossSectionModel('Pouchou 1986', "Pochou & Pichoir in the proceedings from IXCOM 11 (1986)")
BROWN_POWELL = IonizationCrossSectionModel('Brown Powell')
CASNATI1982 = IonizationCrossSectionModel('Casnati 1982', "Casnati82 - E. Casnati, A. Tartari & C. Baraldi, J Phys B15 (1982) 155 as quoted by C. Powell in Ultramicroscopy 28 (1989) 24-31")
GRYZINSKY = IonizationCrossSectionModel('Gryzinsky')
GRYZINSKY_BETHE = IonizationCrossSectionModel('Gryzinsky + Bethe')
JAKOBY = IonizationCrossSectionModel('Jakoby')
BOTE_SALVAT2008 = IonizationCrossSectionModel('Bote and Salvat 2008', 'Bote and Salvat (2008)')
DIJKSTRA_HEIJLIGER1988 = IonizationCrossSectionModel("Dijkstra and Heijliger 1998 (PROZA96)", "G.F. Bastin, J. M. Dijkstra and H.J.M. Heijligers (1998). X-Ray Spectrometry, 27, pp. 3-10")
WORTHINGTON_TOMLIN1956 = IonizationCrossSectionModel('Worthington and Tomlin 1956', 'C.R. Worthington and S.G. Tomlin (1956) The intensity of emission of characteristic x-radiation, Proc. Phys. Soc. A-69, p.401')
HUTCHINS1974 = IonizationCrossSectionModel('Hutchins 1974', 'G.A. Hutchins (1974) Electron Probe Microanalysis, in P.F. Kane and G.B. Larrabee, Characterisation of solid surfaces, Plenum Press, New York, p. 441')

