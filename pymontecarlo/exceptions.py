"""
Exceptions of pymontecarlo.
"""

# Standard library modules.
import textwrap

# Third party modules.

# Local modules.

# Globals and constants variables.

class PymontecarloError(Exception):
    """Base exception of pymontecarlo."""

class ValidationError(PymontecarloError):
    """Exception raised by validators"""

    _textwrapper = textwrap.TextWrapper(initial_indent='  - ',
                                        subsequent_indent=' ' * 4)

    def __init__(self, *causes):
        message = 'Validation failed for the following reasons:\n'
        message += '\n'.join('\n'.join(self._textwrapper.wrap(str(cause)))
                             for cause in causes)
        super().__init__(message)
        self.causes = tuple(causes)
