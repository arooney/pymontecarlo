#!/usr/bin/env python

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2013 Philippe T. Pinard"
__license__ = "GPL v3"

# Standard library modules.
import os
import sys
import glob
from ConfigParser import SafeConfigParser
from subprocess import check_call

# Third party modules.
from paver.easy import task, cmdopts

# Local modules.

# Globals and constants variables.

# Read configuration
_configfilepath = os.path.join(os.path.dirname(__file__), 'pavement.cfg')
if not os.path.exists(_configfilepath):
    raise IOError, 'No configuration "pavement.cfg" found'

config = SafeConfigParser()
config.read(_configfilepath)

def _call_setup(filepath, *args):
    filepath = os.path.abspath(filepath)
    cwd = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    process_args = ('python', filename) + args

    print '--Running %s' % os.path.relpath(filepath, os.curdir)
    check_call(process_args, cwd=cwd)

def _call_all_setups(*args):
    """
    Calls setup.py of pymontecarlo and all programs.
    """
    _call_setup(os.path.join('src', 'core', 'setup.py'), *args)

    for setup_path in glob.glob(os.path.join('src', 'programs', '*', 'setup.py')):
        _call_setup(setup_path, *args)

@task
def clean():
    """
    Cleans all build output from pymontecarlo and programs.
    """
    _call_all_setups('clean', '--all')

@task
def purge():
    """
    Cleans all build and dist output from pymontecarlo and programs.
    """
    _call_all_setups('clean', '--purge')

@task
@cmdopts([('uninstall', 'u', 'Uninstall development mode')])
def develop(options):
    """
    Registers all programs as development mode.
    """
    args = ['-u'] if hasattr(options, 'uninstall') else []

    # casinoTools
    projectdir = config.get('projects', 'casinoTools')
    filepath = os.path.join(projectdir, 'setup_casino2.py')
    _call_setup(filepath, 'develop', *args)

    # winxrayTools
    projectdir = config.get('projects', 'winxrayTools')
    filepath = os.path.join(projectdir, 'setup.py')
    _call_setup(filepath, 'develop', *args)

    # PouchouPichoirModels
    projectdir = config.get('projects', 'PouchouPichoirModels')
    filepath = os.path.join(projectdir, 'setup.py')
    _call_setup(filepath, 'develop', *args)

    # PENELOPE
    projectdir = config.get('projects', 'penelope')
    filepath = os.path.join(projectdir, 'setup.py')
    _call_setup(filepath, 'develop', *args)

    # Core and programs
    _call_all_setups('develop', *args)

@task
def sdist():
    """
    Builds source distribution from pymontecarlo and programs.
    """
    dist_dir = os.path.abspath(os.path.join(os.curdir, 'dist'))
    _call_all_setups('bdist_egg', '-d', dist_dir)

@task
def bdist_egg():
    """
    Builds egg distribution from pymontecarlo and programs.
    """
    dist_dir = os.path.abspath(os.path.join(os.curdir, 'dist'))
    _call_all_setups('bdist_egg', '-d', dist_dir)

    # casinoTools
    projectdir = config.get('projects', 'casinoTools')
    filepath = os.path.join(projectdir, 'setup_casino2.py')
    _call_setup(filepath, 'bdist_egg', '-d', dist_dir)

    # winxrayTools
    projectdir = config.get('projects', 'winxrayTools')
    filepath = os.path.join(projectdir, 'setup.py')
    _call_setup(filepath, 'bdist_egg', '-d', dist_dir)

@task
def test():
    """
    Tests all
    """
    _call_setup('setup.py', 'test')