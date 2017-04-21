""""""

# Standard library modules.

# Third party modules.

# Local modules.
from pymontecarlo.formats.series.options.model.base import ModelSeriesHandler
from pymontecarlo.options.model.ionization_cross_section import IonizationCrossSectionModel
# Globals and constants variables.

class IonizationCrossSectionModelSeriesHandler(ModelSeriesHandler):

    def convert(self, model):
        s = super().convert(model)

        column = self._create_column('ionization cross-section', 'ioniz. xsection')
        s[column] = model.name

        return s

    @property
    def CLASS(self):
        return IonizationCrossSectionModel