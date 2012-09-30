#!/usr/bin/env python
"""
================================================================================
:mod:`config_cli` -- PENEPMA Monte Carlo program CLI configuration
================================================================================

.. module:: config_cli
   :synopsis: PENEPMA Monte Carlo program CLI configuration

.. inheritance-diagram:: pymontecarlo.program.penepma.config_cli

"""

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2012 Philippe T. Pinard"
__license__ = "GPL v3"

# Standard library modules.

# Third party modules.

# Local modules.
from pymontecarlo.program.config_cli import CLI

# Globals and constants variables.

class _PenepmaCLI(CLI):

    def configure(self, console, settings):
        section = settings.add_section('penepma')

        # Pendbase
        question = 'Path to pendbase directory'
        default = getattr(section, 'pendbase', None)
        section.pendbase = \
            console.prompt_directory(question, default, should_exist=True)

        # exe
        question = 'Path to PENEPMA executable'
        default = getattr(section, 'exe', None)
        section.exe = console.prompt_file(question, default, should_exist=True)

        # dumpp
        question = 'Interval between dump (s)'
        default = getattr(section, 'dumpp', None)
        section.dumpp = console.prompt_int(question, default)

cli = _PenepmaCLI()
