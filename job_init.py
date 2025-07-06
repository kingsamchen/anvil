#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 0xCCCCCCCC

from os import path

import os
import pathlib
import shutil

import jinja2
import toml


def get_scaffolds_dir():
    return pathlib.Path(__file__).resolve().parent / 'scaffolds'


class CMakeRule:
    def __init__(self, data):
        self.min_ver = data['min_ver']


class ProjectRule:
    def __init__(self, data):
        # the name is the original name, while upper_name & lower_name both are normalized
        # i.e. `-` is replaced with `_`.
        self.name = data['name']
        self.upper_name = str.upper(self.name).replace('-', '_')
        self.lower_name = str.lower(self.name).replace('-', '_')
        self.cxx_standard = data['cxx_standard']


class PackageManagerRule:
    def __init__(self, data):
        self.use_cpm = data['use_cpm']
        self.use_vcpkg = data['use_vcpkg']


class PCHRule:
    def __init__(self, data):
        self.enabled = data['enabled']


class PlatformSupportRule:
    def __init__(self, data):
        self.support_windows = data['windows']
        self.support_posix = data['posix']


class ModuleRule:
    def __init__(self, data):
        self.name = data['name']
        self.type = data['type']
        self.use_pch = data['use_pch']


class Rules:
    def __init__(self, data):
        self.cmake_rule = CMakeRule(data['cmake'])
        self.project_rule = ProjectRule(data['project'])
        self.package_manager_rule = PackageManagerRule(data['package_manager'])
        self.pch_rule = PCHRule(data['precompiled_header'])
        self.platform_support_rule = PlatformSupportRule(
            data['platform_support'])
        self.module_rule = ModuleRule(data['module'])


def generate_root_cmake_file(rules):
    print('[*] Generating root CMakeLists.txt...')

    src = get_scaffolds_dir() / 'CMakeLists.txt.j2'
    tp = jinja2.Template(src.read_bytes().decode(), keep_trailing_newline=True)
    dest = pathlib.Path('CMakeLists.txt')
    dest.write_bytes(tp.render(
        cmake_min_ver=rules.cmake_rule.min_ver,
        PROJNAME=rules.project_rule.upper_name,
        name=rules.project_rule.name,
        module_name=rules.module_rule.name,
        cxx_standard=rules.project_rule.cxx_standard,
        use_cpm=rules.package_manager_rule.use_cpm,
        use_pch=rules.pch_rule.enabled,
        on_windows=rules.platform_support_rule.support_windows,
        on_posix=rules.platform_support_rule.support_posix,
    ).encode())

    print('[*] Done generating root CMakeLists.txt...')


def setup_cmake_module_folder(rules: Rules):
    print('[*] Setting up cmake modules')

    dest_dir = 'cmake'
    if not path.exists(dest_dir):
        os.mkdir(dest_dir)

    module_dir = path.join(path.dirname(path.abspath(__file__)),
                           'scaffolds',
                           'cmake_modules')

    skip_files = []

    if not rules.package_manager_rule.use_cpm:
        skip_files.append('CPM.cmake')

    if not rules.platform_support_rule.support_posix:
        skip_files.append('compiler_posix.cmake.j2')

    if not rules.platform_support_rule.support_windows:
        skip_files.append('compiler_msvc.cmake.j2')

    used_files = filter(lambda name: name not in skip_files,
                        os.listdir(module_dir))

    for file in used_files:
        shutil.copy(path.join(module_dir, file),
                    path.join(dest_dir, file))

    # Render templates
    for file in os.listdir(dest_dir):
        if file.endswith('.j2'):
            dest_file = pathlib.Path(dest_dir) / file
            dest_file.write_bytes(
                jinja2.Template(dest_file.read_bytes().decode(),
                                keep_trailing_newline=True).render(
                    PROJNAME=rules.project_rule.upper_name,
                    projname=rules.project_rule.lower_name
                ).encode()
            )
            # drop .j2 extension.
            dest_file.rename(dest_file.with_suffix(''))

    print('[*] Done setting up cmake modules')


def generate_module_cmake_file(rules):
    main_dir = rules.module_rule.name
    src = get_scaffolds_dir() / 'module' / 'CMakeLists.txt.j2'
    dest = pathlib.Path(main_dir) / 'CMakeLists.txt'

    tp = jinja2.Template(src.read_bytes().decode(), keep_trailing_newline=True)
    module = {
        'name': rules.module_rule.name,
        'type': rules.module_rule.type,
        'use_pch': rules.pch_rule.enabled and rules.module_rule.use_pch,
    }
    dest.write_bytes(tp.render(
        PROJNAME=rules.project_rule.upper_name,
        projname=rules.project_rule.lower_name,
        module=module
    ).encode())


def touch_main_source_file(rules):
    main_dir = rules.module_rule.name
    src = pathlib.Path(__file__).resolve().parent / \
        'scaffolds' / 'module' / 'main.cpp'
    dest = pathlib.Path(main_dir) / 'main.cpp'
    shutil.copy(src, dest)


def setup_cmake_presets(rule_file, rules):
    print('[*] Setting up CMake Presets')

    src = pathlib.Path(__file__).resolve().parent / \
        'scaffolds' / 'CMakePresets.json.j2'
    dest = pathlib.Path(rule_file).parent / 'CMakePresets.json'

    tp = jinja2.Template(src.read_bytes().decode(), keep_trailing_newline=True)
    out = tp.render(PROJNAME=rules.project_rule.upper_name,
                    use_cpm=rules.package_manager_rule.use_cpm,
                    use_vcpkg=rules.package_manager_rule.use_vcpkg)

    dest.write_bytes(out.encode())

    print('[*] Done setting up CMake Presets')


def setup_clang_format_file(rule_file):
    print('[*] Setting up clang-format file')

    f = '.clang-format'

    shutil.copy(path.join(path.dirname(path.abspath(__file__)), 'scaffolds', f),
                path.join(path.dirname(rule_file), f))

    print('[*] Done setting up .clang-format')


def setup_clang_tidy_file(rule_file, rules):
    print('[*] Setting up clang-tidy file')

    src = pathlib.Path(__file__).resolve().parent / \
        'scaffolds' / '.clang-tidy.j2'
    dest = pathlib.Path(rule_file).parent / '.clang-tidy'
    tp = jinja2.Template(src.read_bytes().decode(), keep_trailing_newline=True)
    dest.write_bytes(
        tp.render(module_name=rules.module_rule.name).encode())

    print('[*] Done setting up .clang-tidy')


def setup_vcpkg_manifest(rule_file, rules: Rules):
    if not rules.package_manager_rule.use_vcpkg:
        return

    print('[*] Setting up vcpkg manifest file')

    src = pathlib.Path(__file__).resolve().parent / \
        'scaffolds' / 'vcpkg.json.j2'
    dest = pathlib.Path(rule_file).parent / 'vcpkg.json'
    tp = jinja2.Template(src.read_bytes().decode(), keep_trailing_newline=True)
    dest.write_bytes(
        tp.render(
            projname=rules.project_rule.lower_name.replace('_', '-')).encode())

    print('[*] Done setting up vcpkg manifest file')


def setup_module(rules):
    module_dir = rules.module_rule.name
    if not path.exists(module_dir):
        os.mkdir(module_dir)
    generate_module_cmake_file(rules)
    touch_main_source_file(rules)
    print(f'[*] Done setting up module {rules.module_rule.name}')


def add_module(args):
    data = toml.load(args.rule_file)
    rules = Rules(data)
    setup_module(rules)


def run_init_job(args):
    data = toml.load(args.rule_file)
    rules = Rules(data)
    generate_root_cmake_file(rules)
    setup_cmake_module_folder(rules)
    setup_cmake_presets(args.rule_file, rules)
    setup_clang_format_file(args.rule_file)
    setup_clang_tidy_file(args.rule_file, rules)
    setup_vcpkg_manifest(args.rule_file, rules)
    setup_module(rules)
