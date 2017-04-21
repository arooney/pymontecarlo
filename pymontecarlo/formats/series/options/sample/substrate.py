""""""

# Standard library modules.

# Third party modules.

# Local modules.
from pymontecarlo.formats.series.options.sample.base import SampleSeriesHandler
from pymontecarlo.options.sample.substrate import SubstrateSample

# Globals and constants variables.

class SubstrateSampleSeriesHandler(SampleSeriesHandler):

    def convert(self, sample):
        s = super().convert(sample)

        s_material = self._convert_serieshandlers(sample.material)
        s_material = self._update_with_prefix(s_material, 'substrate ', 'subs. ')
        s = s.append(s_material)

        return s

    @property
    def CLASS(self):
        return SubstrateSample
