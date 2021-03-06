""""""

# Standard library modules.
import os
import argparse
import multiprocessing
import logging
logger = logging.getLogger(__name__)

# Third party modules.
import tabulate

# Local modules.
import pymontecarlo
from pymontecarlo.exceptions import ProgramNotFound

# Globals and constants variables.

def _create_parser():
    prog = 'pymontecarlo'
    description = 'Run, configure pymontecarlo'
    parser = argparse.ArgumentParser(prog=prog, description=description)

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Run in debug mode')
    parser.add_argument('--programs', action='store_true',
                        help='List available and configured programs')

    return parser

def _create_commands(parser):
    subparsers = parser.add_subparsers(title='Commands', dest='command')
    _create_run_command(subparsers.add_parser('run'))
    _create_config_command(subparsers.add_parser('config'))

def _create_run_command(parser):
    parser.description = 'Run simulation(s) and save results in a project.'

    nprocessors = multiprocessing.cpu_count()

    parser.add_argument('-o', required=False, metavar='FILE',
                        help='Path to project')
    parser.add_argument('-s', action='store_true',
                        help='Skip existing simulations in project')
    parser.add_argument('-n', type=int, default=nprocessors,
                        help='Number of processors to use')

def _create_config_command(parser):
    parser.description = 'Configure pymontecarlo and Monte Carlo programs.'

    # Programs
    subparsers_programs = parser.add_subparsers(title='Programs', dest='program')

    for clasz in pymontecarlo.settings.available_programs:
        configurator = clasz.create_configurator()
        identifier = clasz.getidentifier()
        try:
            program = pymontecarlo.settings.get_activated_program(identifier)
        except ProgramNotFound:
            program = None

        parser_program = subparsers_programs.add_parser(identifier)

        group_activation = parser_program.add_mutually_exclusive_group(required=True)
        group_activation.add_argument('--activate', action='store_true',
                                      help='Activate program')
        group_activation.add_argument('--deactivate', action='store_false',
                                      help='Deactivate program')

        try:
            configurator.prepare_parser(parser_program, program)
        except:
            logger.exception('Prepare parser failed')
            subparsers_programs._name_parser_map.pop(identifier)

def _parse(parser, ns):
    if ns.verbose:
        logger.setLevel(logging.DEBUG)

    if ns.programs:
        header = ['Program', 'Available', 'Activated', 'Details']
        rows = []
        for clasz in pymontecarlo.settings.available_programs:
            configurator = clasz.create_configurator()
            identifier = clasz.getidentifier()
            try:
                program = pymontecarlo.settings.get_activated_program(identifier)
            except ProgramNotFound:
                program = None
            activated = program is not None

            details = []
            if activated:
                dummy = argparse.ArgumentParser()
                configurator.prepare_parser(dummy, program)
                for action in dummy._actions:
                    if action.default == argparse.SUPPRESS:
                        continue
                    details.append('{}: {}'.format(action.dest, action.default))

            rows.append([identifier, True, activated, ', '.join(details)])

        parser.exit(message=tabulate.tabulate(rows, header) + os.linesep)

def _parse_commands(parser, ns):
    if ns.command == 'run':
        _parse_run_command(parser, ns)
        parser.parse_args(['run', '--help'])

    if ns.command == 'config':
        _parse_config_command(parser, ns)
        parser.parse_args(['config', '--help'])

def _parse_run_command(parser, ns):
    pass

def _parse_config_command(parser, ns):
    if ns.program:
        settings = pymontecarlo.settings

        identifier = ns.program
        program_class = settings.get_available_program_class(identifier)

        # Create program
        configurator = program_class.create_configurator()
        if ns.activate:
            program = configurator.create_program(ns, program_class)

            # Validate
            try:
                validator = program.create_validator()
                validator.validate_program(program, None)
            except Exception as ex:
                parser.error(str(ex))

        # Remove existing program
        settings.deactivate_program(identifier)

        # Add new program
        if ns.activate:
            settings.activate_program(program)

        # Save settings
        settings.write()
        parser.exit(message='Settings updated and saved' + os.linesep)

def main():
    parser = _create_parser()
    _create_commands(parser)

    ns = parser.parse_args()

    _parse(parser, ns)
    _parse_commands(parser, ns)
    parser.print_help()

if __name__ == '__main__':
    main()
