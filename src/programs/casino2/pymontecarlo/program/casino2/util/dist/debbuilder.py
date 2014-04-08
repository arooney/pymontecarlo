#!/usr/bin/env python
"""
================================================================================
:mod:`builder` -- Casino2 debian builder
================================================================================

.. module:: builder
   :synopsis: Casino2 debian builder

.. inheritance-diagram:: pymontecarlo.program.casino2.util.dist.deb.builder

"""

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2014 Philippe T. Pinard"
__license__ = "GPL v3"

# Standard library modules.
import os
import zipfile
import tempfile
from datetime import datetime
import shutil

# Third party modules.

# Local modules.
from pymontecarlo.util.dist.debbuilder import _DebBuilder, extract_exe_info

# Globals and constants variables.

class Casino2DebBuilder(_DebBuilder):

    def __init__(self, zip_path):
        self._zip_path = zip_path

        # Exe info
        temp_file = tempfile.NamedTemporaryFile(suffix='.exe', delete=False)
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                for filename in z.namelist():
                    if filename.endswith('wincasino2.exe'):
                        break
                temp_file.write(z.read(filename))
                temp_file.close()
            self._exe_info = extract_exe_info(temp_file.name)
        finally:
            os.remove(temp_file.name)

        _DebBuilder.__init__(self,
                             package='casino2',
                             fullname='Casino 2',
                             version=self._exe_info['File version'], # dummy
                             maintainer='Hendrix Demers <hendrix.demers@mail.mcgill.ca>',
                             authors=['D. Drouin', 'A.R. Couture', 'R. Gauvin',
                                      'P. Hovington', 'P. Horny', 'H. Demers',
                                      'D. Joly', 'P. Drouin', 'N. Poirier-Demers'],
                             section='science',
                             short_description='Monte Carlo simulation of electron trajectory in solid',
                             long_description='The CASINO acronym has been derived from the words "monte CArlo SImulation of electroN trajectory in sOlids". This program is a Monte Carlo simulation of electron trajectory in solid specially designed for low beam interaction in a bulk and thin foil. This complex single scattering Monte Carlo program is specifically designed for low energy beam interaction and can be used to generate many of the recorded signals (X-rays and backscattered electrons) in a scanning electron microscope. This program can also be efficiently used for all of the accelerated voltage found on a field emission scanning electron microscope(0.1 to 30 KeV).',
                             date=datetime.strptime(self._exe_info['Link date'], '%I:%M %p %d/%m/%Y'), # dummy
                             license='We clain no responsibility and liability concerning the technical predictions of this program. In all publications using the results of this program, the complete references to CASINO must be include in the paper.',
                             homepage='http://www.gel.usherbrooke.ca/casino/',
                             depends=['wine'])

    def _extract_zip(self, temp_dir, *args, **kwargs):
        dirpath = os.path.join(temp_dir, 'zip')
        os.makedirs(dirpath)
        with zipfile.ZipFile(self._zip_path, 'r') as z:
            for filename in z.namelist(): # Cannot use extract all, problem in zip
                z.extract(filename, dirpath)

    def _reorganize_files(self, temp_dir, *args, **kwargs):
        def _find(name, path):
            for root, _dirs, files in os.walk(path):
                if name in files:
                    return os.path.join(root, name)

        os.makedirs(os.path.join(temp_dir, 'DEBIAN'))
        os.makedirs(os.path.join(temp_dir, 'usr', 'bin'))
        os.makedirs(os.path.join(temp_dir, 'usr', 'share', self._package))
        os.makedirs(os.path.join(temp_dir, 'usr', 'share', 'man', 'man1'))
        os.makedirs(os.path.join(temp_dir, 'usr', 'share', 'doc', self._package))

        src_dir = os.path.join(temp_dir, 'zip')
        dst_dir = os.path.join(temp_dir, 'usr', 'share', self._package)
        for filename in os.listdir(src_dir):
            shutil.move(os.path.join(src_dir, filename), dst_dir)

        arch = kwargs['arch']
        if arch == 'amd64':
            os.remove(os.path.join(temp_dir, 'usr', 'share',
                                   self._package, 'wincasino2.exe'))
        elif arch == 'i386':
            os.remove(os.path.join(temp_dir, 'usr', 'share',
                                   self._package, 'wincasino2_64.exe'))

        shutil.rmtree(src_dir)

    def _create_executable(self, temp_dir, *args, **kwargs):
        arch = kwargs['arch']
        if arch == 'amd64':
            filename = 'wincasino2_64.exe'
        elif arch == 'i386':
            filename = 'wincasino2.exe'

        lines = []
        lines.append('#!/bin/sh')
        lines.append('cd /usr/share/%s' % self._package)
        lines.append('wine /usr/share/%s/%s $@' % (self._package, filename))
        return lines

    def _write_executable(self, lines, temp_dir, *args, **kwargs):
        filepath = os.path.join(temp_dir, 'usr', 'bin', 'casino2')
        with open(filepath, 'w') as fp:
            fp.write('\n'.join(lines))
        os.chmod(filepath, 0o555)

    def _create_control(self, temp_dir, *args, **kwargs):
        control = _DebBuilder._create_control(self, temp_dir, *args, **kwargs)
        control['Architecture'] = kwargs['arch']
        return control

    def _build(self, temp_dir, *args, **kwargs):
        self._extract_zip(temp_dir, *args, **kwargs)
        self._reorganize_files(temp_dir, *args, **kwargs)

        lines = self._create_executable(temp_dir, *args, **kwargs)
        self._write_executable(lines, temp_dir, *args, **kwargs)

        control = self._create_control(temp_dir, *args, **kwargs)
        self._write_control(control, temp_dir, *args, **kwargs)

        lines = self._create_preinst(temp_dir, *args, **kwargs)
        self._write_preinst(lines, temp_dir, *args, **kwargs)

        lines = self._create_postinst(temp_dir, *args, **kwargs)
        self._write_postinst(lines, temp_dir, *args, **kwargs)

        lines = self._create_prerm(temp_dir, *args, **kwargs)
        self._write_prerm(lines, temp_dir, *args, **kwargs)

        lines = self._create_postrm(temp_dir, *args, **kwargs)
        self._write_postrm(lines, temp_dir, *args, **kwargs)

        lines = self._create_man_page(temp_dir, *args, **kwargs)
        self._write_man_page(lines, temp_dir, *args, **kwargs)

        lines = self._create_copyright(temp_dir, *args, **kwargs)
        self._write_copyright(lines, temp_dir, *args, **kwargs)

        changelog = self._create_changelog(temp_dir, *args, **kwargs)
        self._write_changelog(changelog, temp_dir, *args, **kwargs)

    def build(self, outputdir, *args, **kwargs):
        if 'arch' not in kwargs:
            raise ValueError('Plese specify the architecture: amd64 or i386')
        _DebBuilder.build(self, outputdir, *args, **kwargs)
