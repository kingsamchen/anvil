#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 0xCCCCCCCC


def parse_configuration_set(config_set, config_name, target_name=None, mode_name=None):
    if config_name not in config_set:
        return None, None, None

    config = config_set[config_name]

    gen_target = None
    if target_name is not None:
        for target in config['gen']:
            if target['target'] == target_name:
                gen_target = target
                break

    build_mode = None
    if mode_name is not None:
        for build in config['build']:
            if build['mode'] == mode_name:
                build_mode = build
                break

    return config, gen_target, build_mode
