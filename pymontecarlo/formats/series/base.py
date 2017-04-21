""""""

# Standard library modules.
import abc
import math

# Third party modules.
import pandas as pd

# Local modules.
from pymontecarlo.exceptions import ConvertError
from pymontecarlo.util.entrypoint import resolve_entrypoints

# Globals and constants variables.
ENTRYPOINT_SERIESHANDLER = 'pymontecarlo.formats.series'

def find_convert_serieshandler(obj):
    for clasz in resolve_entrypoints(ENTRYPOINT_SERIESHANDLER):
        handler = clasz()
        if handler.can_convert(obj):
            return handler
    raise ConvertError("No handler found for object {!r}".format(obj))

class SeriesColumn:

    def __init__(self, name, abbrev, unit=None, tolerance=None):
        self._name = name
        self._abbrev = abbrev
        self._unit = unit
        self._tolerance = tolerance

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        return type(self) == type(other) and self.name == other.name

    def __hash__(self):
        # NOTE: To allow slicing of series using only name
        return hash(self.name)

    def __repr__(self):
        return '<{}({})>'.format(self.__class__.__name__, self.name)

    def __str__(self):
        return self.name

    def compare(self, value0, value1):
        if self.tolerance is None:
            return value0 == value1
        else:
            return math.isclose(value0, value1, abs_tol=self.tolerance)

    @property
    def name(self):
        return self._name

    @property
    def abbrev(self):
        return self._abbrev

    @property
    def unit(self):
        return self._unit

    @property
    def tolerance(self):
        return self._tolerance

class SeriesHandler(object, metaclass=abc.ABCMeta):

    def _create_column(self, name, abbrev=None, unit=None, tolerance=None):
        return SeriesColumn(name, abbrev, unit, tolerance)

    def _update_with_prefix(self, s, prefix, prefix_abbrev=None):
        if prefix_abbrev is None:
            prefix_abbrev = prefix

        s_new = pd.Series()

        for column, value in s.items():
            name = prefix + column.name
            abbrev = prefix_abbrev + column.abbrev
            unit = column.unit
            tolerance = column.tolerance
            column_new = self._create_column(name, abbrev, unit, tolerance)
            s_new[column_new] = value

        return s_new

    def _convert_serieshandlers(self, obj):
        return find_convert_serieshandler(obj).convert(obj)

    def can_convert(self, obj):
        return type(obj) is self.CLASS

    @abc.abstractmethod
    def convert(self, obj):
        return pd.Series()

    @abc.abstractproperty
    def CLASS(self):
        raise NotImplementedError

    @property
    def VERSION(self):
        return 1
