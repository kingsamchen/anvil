#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 0xCCCCCCCC

from os import path

import shlex
import subprocess

import toml

import configuration_set_parse as parse
import job_gen


ANVIL_DIR = '.anvil'
CONF = 'configs.toml'


def unpack(*args):
    return args


def run(cmd):
    subprocess.call(shlex.split(cmd))


def run_build_job(args):
    project_root = path.abspath(path.curdir)

    if not args.no_gen:
        status = job_gen.run_gen_job(args)
        if not status:
            return False

    conf_file = path.join(project_root, ANVIL_DIR, CONF)
    if not path.exists(conf_file):
        print('[*] ERROR: Cannot find configuration file at %s' % conf_file)
        return False

    configs = toml.load(conf_file)
    config_name, target_value = unpack(*((str.split(args.target, '.') + [''])[0:2]))
    config, gen_target, build_mode = parse.parse_configuration_set(configs, config_name, target_value, args.build_mode)

    if not config:
        print('[*] ERROR: Cannot find configuration %s' % config_name)
        return False

    if not gen_target:
        print('[*] ERROR: Cannot find gen target %s under configuration %s' % (target_value, config_name))
        return False

    if not build_mode:
        print('[*] ERROR: Cannot find build mode %s under configuration %s' % (args.build_mode, config_name))
        return False

    run('cmake --build "{out_dir}" {args}'.format(
        out_dir=path.join(project_root, gen_target['out_dir']),
        args=build_mode['args']
    ))

    return True
