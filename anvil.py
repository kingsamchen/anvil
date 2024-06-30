#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 0xCCCCCCCC

import argparse
import os
import pathlib
import shutil

import job_init

VER = '0.13.20240630'


def show_anvil_version(_):
    print('anvil %s' % VER)


def touch_project_rules(_):
    fp = pathlib.Path(__file__).resolve().parent / 'project_rules.toml'
    shutil.copy(fp, os.curdir)


def parse_args():
    parser = argparse.ArgumentParser()

    cmd_parser = parser.add_subparsers(title='commands', dest='command')
    cmd_parser.required = True

    # touch project rules toml file.
    touch_parser = cmd_parser.add_parser(
        'touch', help='create project rules file')
    touch_parser.set_defaults(func=touch_project_rules)

    # command init
    init_parser = cmd_parser.add_parser('init', help='bootstrap a new project')
    init_parser.set_defaults(func=job_init.run_init_job)
    init_parser.add_argument(
        'rule_file', help='path to the rule file to bootstrap the project',
        action='store')

    # command version
    ver_parser = cmd_parser.add_parser('version', help='show version and exit')
    ver_parser.set_defaults(func=show_anvil_version)

    return parser.parse_args()


def main():
    args = parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
