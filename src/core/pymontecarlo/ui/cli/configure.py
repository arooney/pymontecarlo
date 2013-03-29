#!/usr/bin/env python
"""
================================================================================
:mod:`configure` -- Script to configure settings
================================================================================

.. module:: configure
   :synopsis: Script to configure settings

"""

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2012 Philippe T. Pinard"
__license__ = "GPL v3"

# Standard library modules.
import os

# Third party modules.

# Local modules.
from pymontecarlo.settings import load_settings, Settings
from pymontecarlo.ui.cli.console import Console

# Globals and constants variables.

def run(argv=None):
    # Initialize
    console = Console()
    console.init()

    console.print_message("Configuration of pyMonteCarlo")
    console.print_line()

    # Find settings.cfg
    filepath = os.path.join(os.path.expanduser('~'), '.pymontecarlo', 'settings.cfg')
    if os.path.exists(filepath):
        console.print_message("A settings.cfg was found in '%s'" % filepath)

        answer = console.prompt_boolean("Do you want to overwrite these settings?", False)
        if not answer:
            console.close()

        settings = load_settings([filepath])
    else:
        console.print_message("No settings.cfg was found. This wizard will help you create one.")
        console.print_message("The settings.cfg will be saved in %s" % filepath)

        settings = Settings() # Empty settings

    console.print_line()

    # Programs
    programs = []

    for program_alias in settings.get_available_program_aliases():
        default = program_alias in settings.get_program_aliases()
        answer = \
            console.prompt_boolean("Do you want to setup %s?" % program_alias, default)
        if answer:
            cli = settings.get_program_cli(program_alias)
            try:
                pass
            except Exception as ex:
                console.print_exception(ex)
                return

            cli.configure(console, settings)

            programs.append(program_alias)
        else:
            if program_alias in settings:
                delattr(settings, program_alias)

        console.print_line()

    # Save
    settings.add_section('pymontecarlo').programs = ','.join(programs)

    dirname = os.path.dirname(filepath)
    if not os.path.exists(dirname):
        os.mkdir(dirname)

    with open(filepath, 'w') as fileobj:
        settings.write(fileobj)
    console.print_success("Settings saved in %s" % filepath)

    # Finalize
    console.close()

if __name__ == '__main__':
    run()
