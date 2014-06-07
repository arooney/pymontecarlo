#!/usr/bin/env python
"""
================================================================================
:mod:`local` -- Local runner and creator
================================================================================

.. module:: local
   :synopsis: Local runner and creator

.. inheritance-diagram:: pymontecarlo.runner.local

"""

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2013 Philippe T. Pinard"
__license__ = "GPL v3"

# Standard library modules.
import os
import logging
import tempfile
import shutil
import queue
import random
import threading

# Third party modules.

# Local modules.
from pymontecarlo.runner.base import \
    _Runner, _RunnerOptionsDispatcher, _RunnerResultsDispatcher
from pymontecarlo.results.results import Results
from pymontecarlo.fileformat.results.results import \
    append as append_results

# Globals and constants variables.

class _LocalRunnerOptionsDispatcher(_RunnerOptionsDispatcher):

    def __init__(self, queue_options, queue_results, outputdir, workdir=None):
        _RunnerOptionsDispatcher.__init__(self, queue_options, queue_results)

        self._worker = None
        self._options = None
        self._outputdir = outputdir
        self._workdir = workdir
        self._user_defined_workdir = self._workdir is not None

    def _run(self):
        while not self.is_cancelled():
            # Retrieve options
            try:
                base_options, options = self._queue_options.get(timeout=0.1)
            except queue.Empty:
                continue

            try:
                # Create working directory
                if not self._user_defined_workdir:
                    workdir = tempfile.mkdtemp()
                else:
                    workdir = self._workdir
                logging.debug('Work directory: %s', workdir)

                # Run
                logging.debug('Running program specific worker')
                self.options_running.fire(options)

                self._options = options
                program = next(iter(options.programs))
                self._worker = program.worker_class(program)
                self._worker.reset()
                container = self._worker.run(options, self._outputdir, workdir)
                self._options = None

                self.options_simulated.fire(options)
                logging.debug('End program specific worker')

                # Cleanup
                if not self._user_defined_workdir:
                    shutil.rmtree(workdir, ignore_errors=True)
                    logging.debug('Removed temporary work directory: %s', workdir)

                # Put results in queue
                self._queue_results.put(Results(base_options, [container]))
            except Exception as ex:
                self.options_error.fire(options, ex)
            finally:
                self._worker = None
                self._queue_options.task_done()

    def cancel(self):
        if self._worker:
            self._worker.cancel()
        _RunnerOptionsDispatcher.cancel(self)

    @property
    def current_options(self):
        return self._options

    @property
    def progress(self):
        if self._worker is None:
            return 0.0
        return self._worker.progress

    @property
    def status(self):
        if self._worker is None:
            return ''
        return self._worker.status

class _LocalRunnerResultsDispatcher(_RunnerResultsDispatcher):

    def __init__(self, queue_results, outputdir, write_lock):
        _RunnerResultsDispatcher.__init__(self, queue_results)

        self._outputdir = outputdir

        self._write_lock = write_lock

    def _run(self):
        while not self.is_cancelled():
            # Retrieve results
            try:
                results = self._queue_results.get(timeout=0.1)
                print(results)
            except queue.Empty:
                continue

            try:
                self._update_status(random.random(),
                                    'Saving %s' % results.options.name)
                h5filepath = os.path.join(self._outputdir,
                                          results.options.name + '.h5')

                with self._write_lock:
                    if os.path.exists(h5filepath):
                        append_results(results, h5filepath)
                    else:
                        results.write(h5filepath)

                self.results_saved.fire(results)
            except Exception as ex:
                self.results_error.fire(results, ex)
            finally:
                self._queue_results.task_done()

class LocalRunner(_Runner):

    def __init__(self, outputdir, workdir=None, overwrite=True,
                 max_workers=1):
        """
        Creates a new runner to run several simulations.

        Use :meth:`put` to add simulation to the run and then use the method
        :meth:`start` to start the simulation(s).
        Status of the simulations can be retrieved using the method
        :meth:`report`.
        The method :meth:`join` before closing an application to ensure that
        all simulations were run and all workers are stopped.

        :arg program: program used to run the simulations

        :arg outputdir: output directory for saving the results from the
            simulation. The directory must exists.

        :arg workdir: work directory for the simulation temporary files.
            If ``None``, a temporary folder is created and removed after each
            simulation is run. If not ``None``, the directory must exists.

        :arg overwrite: whether to overwrite already existing simulation file(s)

        :arg nbprocesses: number of processes/threads to use (default: 1)
        """
        if not os.path.isdir(outputdir):
            raise ValueError('Output directory (%s) is not a directory' % outputdir)
        self._outputdir = outputdir

        if workdir is not None and not os.path.isdir(workdir):
            raise ValueError('Work directory (%s) is not a directory' % workdir)
        self._workdir = workdir

        self._overwrite = overwrite

        self._write_lock = threading.Lock()

        _Runner.__init__(self, max_workers)

    def _create_options_dispatcher(self):
        return _LocalRunnerOptionsDispatcher(self._queue_options,
                                             self._queue_results,
                                             self.outputdir, self.workdir)

    def _create_results_dispatcher(self):
        return _LocalRunnerResultsDispatcher(self._queue_results,
                                             self.outputdir,
                                             self._write_lock)

    def put(self, options):
        h5filepath = os.path.join(self.outputdir, options.name + '.h5')
        if os.path.exists(h5filepath):
            if self._overwrite:
                os.remove(h5filepath)

                lockfilepath = h5filepath + '.lock'
                if os.path.exists(lockfilepath):
                    os.remove(lockfilepath)
            else:
                raise IOError('Results already exists: %s' % h5filepath)

        return _Runner.put(self, options)

    @property
    def outputdir(self):
        return self._outputdir

    @property
    def workdir(self):
        return self._workdir

class _LocalImporterOptionsDispatcher(_RunnerOptionsDispatcher):

    def __init__(self, queue_options, queue_results, outputdir):
        _RunnerOptionsDispatcher.__init__(self, queue_options, queue_results)

        self._worker = None
        self._options = None
        self._outputdir = outputdir

    def _run(self):
        while not self.is_cancelled():
            # Retrieve options
            try:
                base_options, options = self._queue_options.get(timeout=0.1)
            except queue.Empty:
                continue

            try:
                # Run
                logging.debug('Running program specific worker')
                self.options_running.fire(options)

                self._options = options
                program = next(iter(options.programs))
                if not program.autorun:
                    self._worker = program.worker_class(program)
                    self._worker.reset()
                    container = self._worker.import_(options, self._outputdir)
                    self._options = None

                    self.options_simulated.fire(options)
                    logging.debug('End program specific worker')

                    # Put results in queue
                    self._queue_results.put(Results(base_options, [container]))
            except Exception as ex:
                self.options_error.fire(options, ex)
            finally:
                self._worker = None
                self._queue_options.task_done()

    def cancel(self):
        if self._worker:
            self._worker.cancel()
        _RunnerOptionsDispatcher.cancel(self)

    @property
    def current_options(self):
        return self._options

    @property
    def progress(self):
        if self._worker is None:
            return 0.0
        return self._worker.progress

    @property
    def status(self):
        if self._worker is None:
            return ''
        return self._worker.status

class LocalImporter(_Runner):

    def __init__(self, outputdir, max_workers=1):
        if not os.path.isdir(outputdir):
            raise ValueError('Output directory (%s) is not a directory' % outputdir)
        self._outputdir = outputdir

        self._write_lock = threading.Lock()

        _Runner.__init__(self, max_workers)

    def _create_options_dispatcher(self):
        return _LocalImporterOptionsDispatcher(self._queue_options,
                                               self._queue_results,
                                               self.outputdir)

    def _create_results_dispatcher(self):
        return _LocalRunnerResultsDispatcher(self._queue_results,
                                             self.outputdir,
                                             self._write_lock)

    @property
    def outputdir(self):
        return self._outputdir

#class _LocalCreatorDispatcher(_CreatorDispatcher):
#
#    def __init__(self, program, queue_options, outputdir, overwrite=True):
#        _CreatorDispatcher.__init__(self, program, queue_options)
#
#        self._worker = program.worker_class()
#
#        if not os.path.isdir(outputdir):
#            raise ValueError('Output directory (%s) is not a directory' % outputdir)
#        self._outputdir = outputdir
#
#        self._overwrite = overwrite
#
#        self._close_event = threading.Event()
#        self._closed_event = threading.Event()
#
#    def run(self):
#        while not self._close_event.is_set():
#            try:
#                # Retrieve options
#                options = self._queue_options.get()
#
#                # Check if options already exists
#                xmlfilepath = os.path.join(self._outputdir, options.name + ".xml")
#                if os.path.exists(xmlfilepath) and not self._overwrite:
#                    logging.info('Skipping %s as options already exists', options.name)
#                    self._queue_options.task_done()
#                    continue
#
#                # Run
#                logging.debug('Running program specific worker')
#                self._worker.reset()
#                self._worker.create(options, self._outputdir)
#                logging.debug('End program specific worker')
#
#                self._queue_options.task_done()
#            except Exception:
#                self.stop()
#                self._queue_options.raise_exception()
#
#        self._closed_event.set()
#
#    def stop(self):
#        self._worker.stop()
#
#    def close(self):
#        if not self.is_alive():
#            return
#        self._worker.stop()
#        self._close_event.set()
#        self._closed_event.wait()
#
#    def report(self):
#        return self._worker.report()
#
#class LocalCreator(_Creator):
#
#    def __init__(self, program, outputdir, overwrite=True, nbprocesses=1):
#        """
#        Creates a new creator to create simulation files of several simulations.
#
#        Use :meth:`put` to add simulation to the creation list and then use the
#        method :meth:`start` to start the creation.
#        The method :meth:`join` before closing an application to ensure that
#        all simulations were created and all workers are stopped.
#
#        :arg program: program used to run the simulations
#
#        :arg outputdir: output directory for the simulation files.
#            The directory must exists.
#
#        :arg overwrite: whether to overwrite already existing simulation file(s)
#
#        :arg nbprocesses: number of processes/threads to use (default: 1)
#        """
#        _Creator.__init__(self, program)
#
#        if nbprocesses < 1:
#            raise ValueError("Number of processes must be greater or equal to 1.")
#
#        if not os.path.isdir(outputdir):
#            raise ValueError('Output directory (%s) is not a directory' % outputdir)
#
#        self._dispatchers = []
#        for _ in range(nbprocesses):
#            dispatcher = \
#                _LocalCreatorDispatcher(program, self._queue_options,
#                                        outputdir, overwrite)
#            self._dispatchers.append(dispatcher)
#
#    def start(self):
#        if not self._dispatchers:
#            raise RuntimeError("Runner is closed")
#
#        for dispatcher in self._dispatchers:
#            if not dispatcher.is_alive():
#                dispatcher.start()
#                logging.debug('Started dispatcher: %s', dispatcher.name)
#
#        logging.debug('Runner started')
#
#    def stop(self):
#        for dispatcher in self._dispatchers:
#            dispatcher.stop()
#        logging.debug('Runner stopped')
#
#    def close(self):
#        for dispatcher in self._dispatchers:
#            dispatcher.close()
#        self._dispatchers = []
#        logging.debug('Runner closed')
#
#    def report(self):
#        completed, progress, status = _Creator.report(self)
#
#        for dispatcher in self._dispatchers:
#            progress, status = dispatcher.report()
#            if progress > 0.0 and progress < 1.0: # active worker
#                return completed, progress, status
#
#        return completed, progress, status


