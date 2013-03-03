#!/usr/bin/env python

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2013 Philippe T. Pinard"
__license__ = "GPL v3"

# Standard library modules.

# Third party modules.
from setuptools import setup

# Local modules.
from pymontecarlo.util.dist.command import build_py, clean

# Globals and constants variables.

setup(name="pyMonteCarlo-PENSHOWER",
      version='0.1',
      url='http://pymontecarlo.bitbucket.org',
      description="Python interface for Monte Carlo simulation programs",
      author="Hendrix Demers and Philippe T. Pinard",
      author_email="hendrix.demers@mail.mcgill.ca and philippe.pinard@gmail.com",
      license="GPL v3",
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: End Users/Desktop',
                   'License :: OSI Approved :: GNU General Public License (GPL)',
                   'Natural Language :: English',
                   'Programming Language :: Python',
                   'Operating System :: OS Independent',
                   'Topic :: Scientific/Engineering',
                   'Topic :: Scientific/Engineering :: Physics'],

      packages=['pymontecarlo.program.penshower',
                'pymontecarlo.program.penshower.input',
                'pymontecarlo.program.penshower.output',
                'pymontecarlo.program.penshower.runner'],
      package_dir={'pymontecarlo': '../../../pymontecarlo'},
      
      install_requires=['pyMonteCarlo-PENELOPE>=0.1'],

      cmdclass={'build_py': build_py, 'clean': clean},

      entry_points={'pymontecarlo.program':
                        'penshower=pymontecarlo.program.penshower.config:program',
                    'pymontecarlo.program.cli':
                        'penshower=pymontecarlo.program.penshower.config_cli:cli', }
)
