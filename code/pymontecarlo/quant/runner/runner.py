#!/usr/bin/env python
"""
================================================================================
:mod:`runner` -- Quantification runner
================================================================================

.. module:: runner
   :synopsis: Quantification runner

.. inheritance-diagram:: pymontecarlo.quant.runner.runner

"""

# Script information for the file.
__author__ = "Philippe T. Pinard"
__email__ = "philippe.pinard@gmail.com"
__version__ = "0.1"
__copyright__ = "Copyright (c) 2012 Philippe T. Pinard"
__license__ = "GPL v3"

# Standard library modules.
import logging
from operator import methodcaller

# Third party modules.

# Local modules.
from pymontecarlo.util.queue import Queue
from pymontecarlo.quant.runner.worker import Worker as QuantWorker
from pymontecarlo.runner.runner import Runner as SimRunner

# Globals and constants variables.

class Runner(object):
    def __init__(self, worker_class, iterator_class, outputdir, workdir=None,
                 overwrite=True, max_iterations=50, convergence_limit=1e-5,
                 nbprocesses=1):
        """
        Creates a new runner to run several quantifications.
        
        Use :meth:`put` to add measurement to the run and then use the method
        :meth:`start` to start the quantification. 
        Status of the quantification can be retrieved using the method 
        :meth:`report`. 
        The method :meth:`join` before closing an application to ensure that
        all measurements were run and all workers are stopped.
        
        :arg overwrite: whether to overwrite already existing simulation file(s)
        
        :arg nbprocesses: number of processes/threads to use (default: 1)
        """
        if nbprocesses < 1:
            raise ValueError, "Number of processes must be greater or equal to 1."

        # Split processes between simulation and quantification
        # Quantification is given a higher weight
        nbprocesses1 = max(1, nbprocesses / 2)
        nbprocesses2 = max(1, nbprocesses - nbprocesses1)
        sim_nbprocesses = min(nbprocesses1, nbprocesses2)
        self._nbprocesses = max(nbprocesses1, nbprocesses2)

        # Create simulation runner
        # Simulations are always overwritten to prevent conflict between
        # quantification
        self._runner = SimRunner(worker_class, outputdir, workdir,
                                 True, sim_nbprocesses)

        self._iterator_class = iterator_class
        self._max_iterations = max_iterations
        self._convergence_limit = convergence_limit
        self._overwrite = overwrite

        self._options_names = []
        self._queue_measurements = Queue()
        self._workers = []

    @property
    def outputdir(self):
        """
        Output directory.
        """
        return self._runner.outputdir

    def start(self):
        """
        Starts running the simulations.
        """
        if self._workers:
            raise RuntimeError, 'Already started'

        # Create workers
        self._workers = []
        for _ in range(self._nbprocesses):
            worker = \
                QuantWorker(self._queue_measurements, self._runner,
                            self._iterator_class, self._max_iterations,
                            self._convergence_limit, self._overwrite)
            self._workers.append(worker)

            worker.daemon = True
            worker.start()
            logging.debug('Started worker: %s', worker.name)

    def put(self, measurement):
        """
        Puts a measurement in queue.
        
        An :exc:`ValueError` is raised if a measurement with the same name was
        already added. This error is raised as measurement with the same name 
        would lead to results been overwritten.
           
        :arg measurement: measurement to be added to the queue
        """
        name = measurement.options.name
        if name in self._options_names:
            raise ValueError, 'A measurement with the name (%s) was already added' % name

        self._queue_measurements.put(measurement)
        self._options_names.append(name)

        logging.debug('Measurement "%s" put in queue', name)

    def stop(self):
        """
        Stops all workers and closes the current runner.
        """
        self._runner.stop()
        for worker in self._workers:
            worker.stop()
        self._workers = []

    def is_alive(self):
        """
        Returns whether all options in the queue are simulated.
        """
        all_workers_alive = all(map(methodcaller('is_alive'), self._workers))
        all_tasks_done = self._queue_measurements.are_all_tasks_done()

        return all_workers_alive and not all_tasks_done

    def join(self):
        """
        Blocks until all options have been simulated.
        """
        self._queue_measurements.join()
        self.stop()

    def report(self):
        """
        Returns a tuple of:
        
          * counter of completed quantification
          * the progress of *one* of the currently running quantification 
              (between 0.0 and 1.0)
          * text indicating the status of *one* of the currently running 
              quantification
        """
        completed = len(self._options_names) - self._queue_measurements.unfinished_tasks

        for worker in self._workers:
            progress, status = worker.report()
            if progress > 0.0 and progress < 1.0: # active worker
                return completed, progress, status

        return completed, 0, ''

