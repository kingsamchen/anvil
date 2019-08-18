#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 0xCCCCCCCC

import argparse

import job_build
import job_gen
import job_init
import job_list

VER = '0.1.3'


def show_anvil_version(_):
    print('anvil %s' % VER)


def parse_args():
    parser = argparse.ArgumentParser()

    cmd_parser = parser.add_subparsers(title='commands', dest='command')
    cmd_parser.required = True

    # command init
    init_parser = cmd_parser.add_parser('init', help='bootstrap a new project')
    init_parser.set_defaults(func=job_init.run_init_job)
    init_parser.add_argument('rule_file', help='path to the rule file to bootstrap the project', action='store')

    # command gen
    gen_parser = cmd_parser.add_parser('gen', help='generate build system files out from the cmake files')
    gen_parser.set_defaults(func=job_gen.run_gen_job)
    gen_parser.add_argument('target', help='which target to generate', action='store')

    # command build
    build_parser = cmd_parser.add_parser('build', help='build the project. it will first invoke gen command by default')
    build_parser.set_defaults(func=job_build.run_build_job)
    build_parser.add_argument('target', help='which target to build', action='store')
    build_parser.add_argument('--mode', help='which build mode to use', dest='build_mode', action='store', default='')
    build_parser.add_argument('--no-gen', help='do not generate build system files first', dest='no_gen',
                              action='store_true')

    # command list
    list_parser = cmd_parser.add_parser('list',
                                        help='list available gen targets and build modes for a given configuration')
    list_parser.set_defaults(func=job_list.run_list_job)

    # command version
    ver_parser = cmd_parser.add_parser('version', help='show version and exit')
    ver_parser.set_defaults(func=show_anvil_version)

    return parser.parse_args()


def main():
    args = parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
