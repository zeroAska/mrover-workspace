import argparse
import sys
from buildsys import WorkspaceContext
from invoke.exceptions import UnexpectedExit

from .build import build_dir, clean, build_deps, debug_dir


def clean_dir_name(d):
    if d[-1] == '/':
        return d[:-1]
    return d


def main():
    parser = argparse.ArgumentParser(
            description='Jarvis build system for MRover')
    parser.add_argument('-r', '--root', dest='root_dir',
                        help='give the root directory of the workspace')

    subcommands = parser.add_subparsers(
            title='Subcommands',
            description='valid subcommands',
            help='Actions',
            dest='subcommand_name')
    parser_build = subcommands.add_parser('build', help='Build a directory')
    parser_build.add_argument('dir', help='The directory to build')
    parser_build.add_argument('-o', '--option', dest='build_opt',
                              help='A build option to pass to the underlying '
                              'build system')

    subcommands.add_parser('clean',
                           help='Removes the product env')
    subcommands.add_parser('dep',
                           help='Installs 3rdparty folder into product env')
    subcommands.add_parser('exec',
                           help='Runs a command in the product venv')
    subcommands.add_parser('upgrade',
                           help='Re-installs the Jarvis CLI')

    parser_mbed = subcommands.add_parser('mbed',
                                         help='Runs the mbed CLI')
    parser_mbed.add_argument('mbed_args', nargs='+')

    args = parser.parse_args()

    try:
        ctx = WorkspaceContext(args.root_dir)

        if args.subcommand_name == 'build':
            build_deps(ctx)
            opt = None
            if args.build_opt:
                opt = args.build_opt.split('=')[0:2]
                print('option is {}'.format(opt))
            build_dir(ctx, clean_dir_name(args.dir), opt)
        elif args.subcommand_name == 'clean':
            clean(ctx)
        elif args.subcommand_name == 'dep':
            build_deps(ctx)
        elif args.subcommand_name == 'mbed':
            with ctx.inside_mbed_env():
                ctx.run('mbed {}'.format(
                    ' '.join('"{}"'.format(arg) for arg in args.mbed_args)))
    except UnexpectedExit as e:
        sys.exit(e.result.exited)


if __name__ == "__main__":
    main()
