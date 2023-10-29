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
        self.use_presets = data['use_presets']


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
        self.pch_file = data['pch_file']


class PlatformSupportRule:
    def __init__(self, data):
        self.support_windows = data['windows']
        self.support_posix = data['posix']


class MainModuleRule:
    def __init__(self, data):
        self.name = data['name']
        self.type = data['type']
        self.use_pch = data['use_pch']
        self.use_msvc_sa = data['use_msvc_static_analysis']


class TestSupportRule:
    def __init__(self, data):
        self.enabled = data['enabled']


class Rules:
    def __init__(self, data):
        self.cmake_rule = CMakeRule(data['cmake'])
        self.project_rule = ProjectRule(data['project'])
        self.package_manager_rule = PackageManagerRule(data['package_manager'])
        self.pch_rule = PCHRule(data['precompiled_header'])
        self.platform_support_rule = PlatformSupportRule(
            data['platform_support'])
        self.main_module_rule = MainModuleRule(data['main_module'])
        self.test_support_rule = TestSupportRule(data['test_support'])


def generate_root_cmake_file(rules):
    print('[*] Generating root CMakeLists.txt...')

    src = get_scaffolds_dir() / 'CMakeLists.txt.j2'
    tp = jinja2.Template(src.read_bytes().decode())
    dest = pathlib.Path('CMakeLists.txt')
    dest.write_bytes(tp.render(
        cmake_min_ver=rules.cmake_rule.min_ver,
        PROJNAME=rules.project_rule.upper_name,
        name=rules.project_rule.name,
        module_name=rules.main_module_rule.name,
        cxx_standard=rules.project_rule.cxx_standard,
        use_cpm=rules.package_manager_rule.use_cpm,
        use_pch=rules.pch_rule.enabled,
        pch_file=rules.pch_rule.pch_file,
        on_windows=rules.platform_support_rule.support_windows,
        on_posix=rules.platform_support_rule.support_posix,
        use_tests=rules.test_support_rule.enabled,
    ).encode())

    print('[*] Done generating root CMakeLists.txt...')


def setup_cmake_module_folder(rules):
    print('[*] Setting up cmake modules')

    dest_dir = 'cmake'
    if not path.exists(dest_dir):
        os.mkdir(dest_dir)

    module_dir = path.join(path.dirname(path.abspath(__file__)),
                           'scaffolds',
                           'cmake_modules')

    if rules.platform_support_rule.support_posix:
        dest_path = path.join(dest_dir, 'compiler_posix.cmake')
        shutil.copy(path.join(module_dir, 'compiler_posix.cmake.j2'), dest_path)

    if rules.platform_support_rule.support_windows:
        dest_path = path.join(dest_dir, 'compiler_msvc.cmake')
        shutil.copy(path.join(module_dir, 'compiler_msvc.cmake.j2'), dest_path)

    cond_files = ('compiler_posix.cmake.j2', 'compiler_msvc.cmake.j2',)
    normal_files = filter(lambda name: name not in cond_files,
                          os.listdir(module_dir))
    for file in normal_files:
        shutil.copy(path.join(module_dir, file),
                    path.join(dest_dir, file.removesuffix('.j2')))

    # Render templates

    files_need_replace = ('compiler_posix.cmake',
                          'compiler_msvc.cmake',
                          'clang_tidy.cmake',)
    to_replace_files = filter(lambda name: name in files_need_replace,
                              os.listdir(dest_dir))
    for file in to_replace_files:
        dest_file = pathlib.Path(dest_dir) / file
        dest_file.write_bytes(
            jinja2.Template(dest_file.read_bytes().decode()).render(
                PROJNAME=rules.project_rule.upper_name,
                projname=rules.project_rule.lower_name
            ).encode()
        )

    print('[*] Done setting up cmake modules')


def setup_pch_files(rules):
    if not rules.pch_rule.enabled:
        return

    print('[*] Setting up pch files')

    pch_folder = path.dirname(rules.pch_rule.pch_file)
    if not path.exists(pch_folder):
        os.makedirs(pch_folder)

    pch_src_dir = path.join(path.dirname(
        path.abspath(__file__)), 'scaffolds', 'pch')

    shutil.copy(path.join(pch_src_dir, 'precompile.h'),
                rules.pch_rule.pch_file)
    shutil.copy(path.join(pch_src_dir, 'precompile.cpp'),
                path.join(pch_folder, 'precompile.cpp'))

    print('[*] Done setting up pch files')


def generate_main_module_cmake_file(rules):
    print('[*] Setting up CMakeLists.txt for main module')

    main_dir = rules.main_module_rule.name

    if not path.exists(main_dir):
        os.mkdir(main_dir)

    src = get_scaffolds_dir() / 'main_module' / 'CMakeLists.txt.j2'
    dest = pathlib.Path(main_dir) / 'CMakeLists.txt'

    tp = jinja2.Template(src.read_bytes().decode())
    module = {
        'name': rules.main_module_rule.name,
        'use_pch': rules.pch_rule.enabled and rules.main_module_rule.use_pch,
        'type': rules.main_module_rule.type,
    }
    dest.write_bytes(tp.render(
        PROJNAME=rules.project_rule.upper_name,
        projname=rules.project_rule.lower_name,
        module=module
    ).encode())

    print('[*] Done setting up CMakeLists.txt for main module')


def touch_main_source_file(rules):
    main_dir = rules.main_module_rule.name
    src = pathlib.Path(__file__).resolve().parent / \
        'scaffolds' / 'main_module' / 'main.cpp'
    dest = pathlib.Path(main_dir) / 'main.cpp'
    shutil.copy(src, dest)


def setup_tests(rules):
    if not rules.test_support_rule.enabled:
        return

    print('[*] Setting up tests')

    src_test_dir = get_scaffolds_dir() / 'tests'
    dest_dir = pathlib.Path('tests')
    if not path.exists(dest_dir):
        os.mkdir(dest_dir)

    test_files = os.listdir(src_test_dir)
    for file in test_files:
        src = src_test_dir / file
        dest = dest_dir / file
        shutil.copy(src, str(dest).removesuffix('.j2'))

    f = dest_dir / 'CMakeLists.txt'
    tp = jinja2.Template(f.read_bytes().decode())
    f.write_bytes(tp.render(
        projname=rules.project_rule.lower_name,
        PROJNAME=rules.project_rule.upper_name
    ).encode())

    print('[*] Done setting up tests')


def setup_anvil_build_scripts(rule_file, rules):
    print('[*] Setting up anvil build scripts')

    if rules.cmake_rule.use_presets:
        f = 'CMakePresets.json'

        shutil.copy(path.join(path.dirname(path.abspath(__file__)),
                              'scaffolds',
                              f),
                    path.join(path.dirname(rule_file), f))
    else:
        src = pathlib.Path(__file__).resolve().parent / \
            'scaffolds' / 'build.py.j2'
        dest = pathlib.Path(rule_file).parent / 'build.py'

        tp = jinja2.Template(src.read_bytes().decode())
        out = tp.render(PROJNAME=rules.project_rule.upper_name)

        dest.write_bytes(out.encode())

    print('[*] Done setting up build scripts')


def setup_clang_format_file(rule_file):
    print('[*] Setting up clang-format file')

    f = '.clang-format'

    shutil.copy(path.join(path.dirname(path.abspath(__file__)), 'scaffolds', f),
                path.join(path.dirname(rule_file), f))

    print('[*] Done setting up .clang-format')


def setup_clang_tidy_file(rule_file, rules):
    print('[*] Setting up clang-tidy file')

    src = pathlib.Path(__file__).resolve().parent / 'scaffolds' \
        / '.clang-tidy.j2'
    dest = pathlib.Path(rule_file).parent / '.clang-tidy'
    tp = jinja2.Template(src.read_bytes().decode())
    dest.write_bytes(
        tp.render(main_module_name=rules.main_module_rule.name).encode())

    print('[*] Done setting up .clang-tidy')


def setup_vcpkg_manifest(rule_file, rules):
    if not rules.package_manager_rule.use_vcpkg:
        return

    print('[*] Setting up vcpkg manifest file')

    src = pathlib.Path(__file__).resolve().parent / 'scaffolds' \
        / 'vcpkg.json.j2'
    dest = pathlib.Path(rule_file).parent / 'vcpkg.json'
    tp = jinja2.Template(src.read_bytes().decode())
    dest.write_bytes(
        tp.render(projname=rules.project_rule.lower_name).encode())

    print('[*] Done setting up vcpkg manifest file')


def run_init_job(args):
    data = toml.load(args.rule_file)
    rules = Rules(data)
    generate_root_cmake_file(rules)
    setup_cmake_module_folder(rules)
    setup_pch_files(rules)
    generate_main_module_cmake_file(rules)
    setup_tests(rules)
    touch_main_source_file(rules)
    setup_anvil_build_scripts(args.rule_file, rules)
    setup_clang_format_file(args.rule_file)
    setup_clang_tidy_file(args.rule_file, rules)
    setup_vcpkg_manifest(args.rule_file, rules)
