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
from pymontecarlo.util.dist.command import clean

# Globals and constants variables.

setup(name="pyMonteCarlo-WinXRay",
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

      packages=['pymontecarlo',
                'pymontecarlo.program',
                'pymontecarlo.program.winxray',
                'pymontecarlo.program.winxray.input',
                'pymontecarlo.program.winxray.output',
                'pymontecarlo.program.winxray.runner'],

      install_requires=['winxrayTools>=0.1'],
      dependency_links=["https://bitbucket.org/pymontecarlo/pymontecarlo/downloads"],

      cmdclass={'clean': clean},

      entry_points={'pymontecarlo.program':
                        'winxray=pymontecarlo.program.winxray.config:program',
                    'pymontecarlo.program.cli':
                        'winxray=pymontecarlo.program.winxray.config_cli:cli',
                    'pymontecarlo.program.gui':
                        'winxray=pymontecarlo.program.winxray.config_gui:gui', },

      test_suite='nose.collector',
)

