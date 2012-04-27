#!/usr/bin/env python
"""
================================================================================
:mod:`pymontecarlo` -- Common interface to several Monte Carlo codes
================================================================================

.. module:: pymontecarlo
   :synopsis: Common interface to several Monte Carlo codes

.. inheritance-diagram:: pymontecarlo

"""

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2011 Philippe T. Pinard"
__license__ = "GPL v3"

# Standard library modules.
import os
import logging

# Third party modules.
from pkg_resources import resource_filename #@UnresolvedImport

# Local modules.
from pymontecarlo.util.config import ConfigParser
from pymontecarlo.util.xmlutil import XMLIO

# Globals and constants variables.

################################################################################
# Register XML namespace and schema
################################################################################

XMLIO.add_namespace('mc', 'http://pymontecarlo.sf.net',
                    resource_filename(__name__, 'schema.xsd'))

################################################################################
# Settings
################################################################################

_settings = None

def get_settings():
    """
    Returns the global settings.
    
    .. note:: 
       
       Note that the settings are loaded only once when this method is called
       for the first time. After that, the same settings are returned.
    
    :return: settings
    :rtype: :class:`pymontecarlo.util.config.ConfigParser`
    """
    global _settings

    if _settings is not None:
        return _settings

    filepaths = []
    filepaths.append(os.path.join(os.path.expanduser('~'), '.pymontecarlo',
                                  'settings.cfg'))
    filepaths.append(os.path.join(os.path.dirname(__file__), 'settings.cfg'))

    _settings = load_settings(filepaths)

    return _settings

def load_settings(filepaths):
    """
    Loads the settings from the first file path that exists from those 
    specified.
    
    :arg filepaths: :class:`list` of paths to potential settings file
    """
    settings = ConfigParser()

    for filepath in filepaths:
        if os.path.exists(filepath):
            logging.debug('Loading settings from: %s', filepath)

            with open(filepath, 'r') as f:
                settings.read(f)
                return settings

    raise IOError, "Settings could not be loaded"

################################################################################
# Programs
################################################################################

_programs = None

def get_programs():
    """
    Returns the available Monte Carlo programs.
    The programs are loaded based on the settings.
    
    .. note:: 
       
       Note that the programs are loaded only once when this method is called
       for the first time. After that, the same set is returned.
    
    :return: a set of programs
    """
    global _programs

    if _programs is not None:
        return _programs

    _programs = frozenset(load_programs(get_settings()))

    return _programs

def load_programs(settings):
    """
    Loads the programs defined in the settings.
    The list of programs should be set under the section ``pymontecarlo`` and
    the option ``program``. An :exc:`IOError` exception is raised if the option
    is not defined.
    
    Before a program is added to the list, the method makes sure that the
    program is valid. 
    
    :arg settings: settings
    """
    programs = set()

    value = getattr(settings.pymontecarlo, 'programs', '')
    if not value:
        raise IOError, "No programs are defined in settings"

    extensions = getattr(settings.pymontecarlo, 'programs').split(',')
    for extension in extensions:
        mod = __import__(extension, None, None, ['config'])

        if not hasattr(mod, 'config'):
            raise ImportError, "Extension '%s' does not have a 'config' module." % extension

        if not hasattr(mod.config, 'program'):
            raise ImportError, "Module 'config' of extension '%s' must have a 'program' attribute" % extension

        program = mod.config.program
        program.validate()

        programs.add(program)
        logging.debug("Loaded program (%s) from %s", program.name, extension)

    return programs

################################################################################
# Reload
################################################################################

def reload():
    """
    Resets the settings and programs.
    Once the methods :meth:`get_settings` or :meth:`get_programs` are called,
    the settings and programs will be reloaded.
    """
    _settings = None
    _programs = None
