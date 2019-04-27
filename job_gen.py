#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 0xCCCCCCCC

import os
import shlex
import subprocess

from os import path

import toml

import configuration_set_parse as parse


ANVIL_DIR = '.anvil'
CONF = 'configs.toml'


def unpack(*args):
    return args


def run(cmd):
    subprocess.call(shlex.split(cmd))


def run_gen_job(args):
    project_root = path.abspath(path.curdir)

    conf_file = path.join(project_root, ANVIL_DIR, CONF)
    if not path.exists(conf_file):
        print('[*] ERROR: Cannot find configuration file at %s' % conf_file)
        return False

    configs = toml.load(conf_file)
    config_name, target_value = unpack(*((str.split(args.target, '.') + [''])[0:2]))
    config, gen_target, _ = parse.parse_configuration_set(configs, config_name, target_value)

    if not config:
        print('[*] ERROR: Cannot find configuration %s' % config_name)
        return False

    if not gen_target:
        print('[*] ERROR: Cannot find gen target %s under configuration %s' % (target_value, config_name))
        return False

    out_dir = path.join(project_root, gen_target['out_dir'])
    if not path.exists(out_dir):
        os.mkdir(out_dir)
    os.chdir(out_dir)

    run('cmake {args} -G "{generator}" "{root}"'.format(
        args=gen_target['args'],
        generator=config['generator'],
        root=project_root
    ))

    return True
