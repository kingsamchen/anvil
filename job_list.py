#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 0xCCCCCCCC

from os import path

import toml


ANVIL_DIR = '.anvil'
CONF = 'configs.toml'


def run_list_job(_):
    project_root = path.abspath(path.curdir)

    conf_file = path.join(project_root, ANVIL_DIR, CONF)
    if not path.exists(conf_file):
        print('[*] ERROR: Cannot find configuration file at %s' % conf_file)
        return

    data = toml.load(conf_file)
    print(toml.dumps(data))
