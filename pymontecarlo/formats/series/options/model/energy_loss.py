""""""

# Standard library modules.

# Third party modules.

# Local modules.
from pymontecarlo.formats.series.options.model.base import ModelSeriesHandler
from pymontecarlo.options.model.energy_loss import EnergyLossModel

# Globals and constants variables.

class EnergyLossModelSeriesHandler(ModelSeriesHandler):

    def convert(self, model):
        s = super().convert(model)

        column = self._create_column('energy loss', 'dE/dS')
        s[column] = model.name

        return s

    @property
    def CLASS(self):
        return EnergyLossModel
