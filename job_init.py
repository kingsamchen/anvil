#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 0xCCCCCCCC

from os import path

import os
import shutil

import toml


_CMAKE_TEMPLATE = 'cmake_minimum_required(VERSION %s)\n\n# Add POLICY below.\n'

_PROJECT_TEMPLATE = '''# Detect if being bundled via sub-directory.
if(NOT DEFINED PROJECT_NAME)
  set({cap_name}_NOT_SUBPROJECT ON)
else()
  set({cap_name}_NOT_SUBPROJECT OFF)
endif()

message(STATUS "{name} as root project = ${{{cap_name}_NOT_SUBPROJECT}}")

project({name} CXX)

set_property(GLOBAL PROPERTY USE_FOLDERS ON)

if({cap_name}_NOT_SUBPROJECT)
  set(CMAKE_CXX_STANDARD {cxx_standard})
  set(CMAKE_CXX_STANDARD_REQUIRED ON)
  set(CMAKE_CXX_EXTENSIONS OFF)

  set(ROOT_DIR ${{CMAKE_SOURCE_DIR}})
endif()

# Add options below.

set({cap_name}_DIR ${{CMAKE_CURRENT_SOURCE_DIR}})
set({cap_name}_CMAKE_DIR ${{{cap_name}_DIR}}/cmake)

include(CTest)
include(${{{cap_name}_CMAKE_DIR}}/CPM.cmake)

message(STATUS "{name} GENERATOR = " ${{CMAKE_GENERATOR}})'''

_PCH_TEMPLATE = '''
set({cap_name}_PCH_HEADER ${{{cap_name}_DIR}}/{pch_file})
'''

_OUTPUT_CONFIG_TEMPLATE = '''# Output configurations.
get_property(MULTICONF_GENERATOR GLOBAL PROPERTY GENERATOR_IS_MULTI_CONFIG)
if({cap_name}_NOT_SUBPROJECT)
  if(MULTICONF_GENERATOR)
    foreach(OUTPUTCONFIG_TYPE ${{CMAKE_CONFIGURATION_TYPES}})
      string(TOUPPER ${{OUTPUTCONFIG_TYPE}} OUTPUTCONFIG)
      set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_${{OUTPUTCONFIG}} ${{CMAKE_BINARY_DIR}}/${{OUTPUTCONFIG_TYPE}}/bin)
      set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY_${{OUTPUTCONFIG}} ${{CMAKE_BINARY_DIR}}/${{OUTPUTCONFIG_TYPE}}/lib)
    endforeach()
  else()
    if(NOT CMAKE_BUILD_TYPE)
      set(CMAKE_BUILD_TYPE "Release")
    endif()
    message(STATUS "{name} BUILD_TYPE = " ${{CMAKE_BUILD_TYPE}})
    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${{CMAKE_BINARY_DIR}}/bin)
    set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${{CMAKE_BINARY_DIR}}/lib)
  endif()
else()
  if(NOT MULTICONF_GENERATOR)
    message(STATUS "{name} BUILD_TYPE = " ${{CMAKE_BUILD_TYPE}})
  endif()
endif()
'''

_COMPILER_MSVC_TEMPLATE = \
        '''include(${{{cap_name}_CMAKE_DIR}}/compiler_msvc.cmake)'''

_COMPILER_POSIX_TEMPLATE = \
        '''include(${{{cap_name}_CMAKE_DIR}}/compiler_posix.cmake)'''

_CLANG_TIDY_TEMPLATE = \
'''include(${{{cap_name}_CMAKE_DIR}}/clang_tidy.cmake)
'''

_ADD_MAIN_MODULE_TEMPLATE = 'add_subdirectory({name})\n'

_MAIN_TARGET_TEMPLATE = '''add_{type}({name})

target_sources({name}
  PRIVATE
    main.cpp

  $<$<BOOL:${{WIN32}}>:
  >

  $<$<NOT:$<BOOL:${{WIN32}}>>:
  >
)

target_include_directories({name}
  PUBLIC ${{CMAKE_CURRENT_SOURCE_DIR}}/../
)

target_link_libraries({name}
)

{low_proj_name}_apply_common_compile_options({name})
'''

_MAIN_OPTIONS_TEMPLATE = '''# TODO: Edit at your will
if(MSVC)
  if({cap_proj_name}_USE_MSVC_PARALLEL_BUILD)
    {low_proj_name}_apply_msvc_parallel_build({name})
  endif()
  if({cap_proj_name}_USE_MSVC_STATIC_ANALYSIS)
    {low_proj_name}_apply_msvc_static_analysis({name}
      WDL
        /wd6011 # Dereferencing potentially NULL pointer.
    )
  endif()
  get_target_property({name}_FILES {name} SOURCES)
  source_group("{name}" FILES ${{{name}_FILES}})
else()
  if({cap_proj_name}_USE_SANITIZER)
    {low_proj_name}_apply_sanitizer({name})
  endif()
endif()
'''

_MAIN_USE_PCH_TEMPLATE = '''target_precompile_headers({name}
  PRIVATE "${{{cap_proj_name}_PCH_HEADER}}"
)
'''

_TEST_SUPPORT_TEMPLATE = '''if({cap_name}_NOT_SUBPROJECT AND BUILD_TESTING)
  add_subdirectory(tests)
endif()
'''

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
        self.pch_rule = PCHRule(data['precompiled_header'])
        self.platform_support_rule = PlatformSupportRule(data['platform_support'])
        self.main_module_rule = MainModuleRule(data['main_module'])
        self.test_support_rule = TestSupportRule(data['test_support'])


def generate_cmake_ver_part(rules):
    return _CMAKE_TEMPLATE % rules.cmake_rule.min_ver


def generate_project_part(rules):
    return _PROJECT_TEMPLATE.format(cap_name=rules.project_rule.upper_name,
                                    name=rules.project_rule.name,
                                    cxx_standard=rules.project_rule.cxx_standard,
                                    main_module_name=rules.main_module_rule.name)


def generate_pch_part(rules):
    if rules.pch_rule.enabled:
        return _PCH_TEMPLATE.format(cap_name=rules.project_rule.upper_name,
                                    pch_file=rules.pch_rule.pch_file)
    else:
        return ''


def indent_lines(s, indent_size):
    return str.join('\n', map(lambda ln: ' ' * indent_size + ln if ln != '' else '',
                              str.splitlines(s)))


def generate_output_conf_part(rules):
    _ = rules
    return _OUTPUT_CONFIG_TEMPLATE.format(
        cap_name=rules.project_rule.upper_name,
        name=rules.project_rule.name)


def generate_compiler_part(rules):
    text = '# Compiler configurations.\n'

    msvc = ''
    posix = ''
    if rules.platform_support_rule.support_windows:
        msvc = _COMPILER_MSVC_TEMPLATE.format(
                cap_name=rules.project_rule.upper_name)
    if rules.platform_support_rule.support_posix:
        posix = _COMPILER_POSIX_TEMPLATE.format(
                cap_name=rules.project_rule.upper_name)

    if msvc != '' and posix != '':
        text += 'if(MSVC)\n'
        text += indent_lines(msvc, 2)
        text += '\nelse()\n'
        text += indent_lines(posix, 2)
        text += '\nendif()\n'
    else:
        text += msvc if msvc != '' else posix
        text += '\n'

    return text


def generate_clang_tidy_part(rules):
    return _CLANG_TIDY_TEMPLATE.format(cap_name=rules.project_rule.upper_name)


def generate_add_main_module_part(rules):
    return _ADD_MAIN_MODULE_TEMPLATE.format(name=rules.main_module_rule.name)


def generate_test_part(rules):
    if rules.test_support_rule.enabled:
        return _TEST_SUPPORT_TEMPLATE.format(
                cap_name=rules.project_rule.upper_name)
    else:
        return ''


def generate_root_cmake_file(rules):
    print('[*] Generating root CMakeLists.txt...')

    with open('CMakeLists.txt', 'w', newline='\n') as f:
        f.write(generate_cmake_ver_part(rules))
        f.write('\n')

        f.write(generate_project_part(rules))
        f.write('\n')

        f.write(generate_pch_part(rules))
        f.write('\n')

        f.write(generate_output_conf_part(rules))
        f.write('\n')

        f.write(generate_compiler_part(rules))
        f.write('\n')

        f.write(generate_clang_tidy_part(rules))
        f.write('\n')

        f.write(generate_add_main_module_part(rules))

        f.write(generate_test_part(rules))

    print('[*] Done generating root CMakeLists.txt...')


def replace_projname_for_files(filepath, project_name, cap_project_name):
    with open(filepath, mode='r+', newline='\n') as f:
        lines = f.readlines()
        for i, _ in enumerate(lines):
            lines[i] = lines[i].replace('{projname}', project_name)
            lines[i] = lines[i].replace('{PROJNAME}', cap_project_name)
        # Let's overwrite
        f.seek(0, os.SEEK_SET)
        f.writelines(lines)
        f.truncate()


def setup_cmake_module_folder(rules):
    print('[*] Setting up cmake modules')

    dest_dir = 'cmake'
    if not path.exists(dest_dir):
        os.mkdir(dest_dir)

    module_dir = path.join(path.dirname(path.abspath(__file__)),
                           'scaffolds',
                           'cmake_modules')

    if rules.platform_support_rule.support_posix:
        file = 'compiler_posix.cmake'
        target_path = path.join(dest_dir, file)
        shutil.copy(path.join(module_dir, file), target_path)

    if rules.platform_support_rule.support_windows:
        file = 'compiler_msvc.cmake'
        target_path = path.join(dest_dir, file)
        shutil.copy(path.join(module_dir, file), target_path)

    cond_files = ('compiler_posix.cmake', 'compiler_msvc.cmake',)
    normal_files = filter(lambda name: name not in cond_files,
                          os.listdir(module_dir))
    for file in normal_files:
        shutil.copy(path.join(module_dir, file), path.join(dest_dir, file))

    # Replace project name placeholders with real name

    files_need_replace = ('compiler_posix.cmake',
                          'compiler_msvc.cmake',
                          'clang_tidy.cmake',)
    to_replace_files = filter(lambda name: name in files_need_replace,
                              os.listdir(dest_dir))
    for file in to_replace_files:
        target_path = path.join(dest_dir, file)
        replace_projname_for_files(target_path,
                                   rules.project_rule.lower_name,
                                   rules.project_rule.upper_name)

    print('[*] Done setting up cmake modules')


def setup_pch_files(rules):
    if not rules.pch_rule.enabled:
        return

    print('[*] Setting up pch files')

    pch_folder = path.dirname(rules.pch_rule.pch_file)
    if not path.exists(pch_folder):
        os.makedirs(pch_folder)

    pch_src_dir = path.join(path.dirname(path.abspath(__file__)), 'scaffolds', 'pch')

    shutil.copy(path.join(pch_src_dir, 'precompile.h'), rules.pch_rule.pch_file)
    shutil.copy(path.join(pch_src_dir, 'precompile.cpp'), path.join(pch_folder, 'precompile.cpp'))

    print('[*] Done setting up pch files')


def generate_main_module_cmake_file(rules):
    print('[*] Setting up CMakeLists.txt for main module')

    main_dir = rules.main_module_rule.name

    if not path.exists(main_dir):
        os.mkdir(main_dir)

    with open(path.join(main_dir, 'CMakeLists.txt'), 'w', newline='\n') as f:
        f.write('\n')

        f.write(_MAIN_TARGET_TEMPLATE.format(
                name=rules.main_module_rule.name,
                type=rules.main_module_rule.type,
                low_proj_name=rules.project_rule.lower_name))

        f.write('\n')
        f.write(_MAIN_OPTIONS_TEMPLATE.format(
                name=rules.main_module_rule.name,
                low_proj_name=rules.project_rule.lower_name,
                cap_proj_name=rules.project_rule.upper_name))

        if rules.pch_rule.enabled and rules.main_module_rule.use_pch:
            f.write('\n')
            f.write(_MAIN_USE_PCH_TEMPLATE.format(
                    name=rules.main_module_rule.name,
                    cap_proj_name=rules.project_rule.upper_name))

    print('[*] Done setting up CMakeLists.txt for main module')


def touch_main_source_file(rules):
    main_dir = rules.main_module_rule.name
    shutil.copy(path.join(path.dirname(path.abspath(__file__)), 'scaffolds', 'main.cpp'),
                path.join(main_dir, 'main.cpp'))


def setup_tests(rules):
    if not rules.test_support_rule.enabled:
        return

    print('[*] Setting up tests')

    src_test_dir = path.join(path.dirname(path.abspath(__file__)),
                             'scaffolds',
                             'tests')
    dest_dir = 'tests'
    if not path.exists(dest_dir):
        os.mkdir(dest_dir)

    test_files = os.listdir(src_test_dir)
    for file in test_files:
        src = path.join(src_test_dir, file)
        dest = path.join(dest_dir, file)
        shutil.copy(src, dest)

    replace_projname_for_files(path.join(dest_dir, 'CMakeLists.txt'),
                               rules.project_rule.lower_name,
                               rules.project_rule.upper_name)

    print('[*] Done setting up tests')


def setup_anvil_build_scripts(rule_file, rules):
    print('[*] Setting up anvil build scripts')

    script_file = 'build.py'

    src = path.join(path.dirname(path.abspath(__file__)),
                    'scaffolds',
                    script_file)
    dest = path.join(path.dirname(rule_file), script_file)
    shutil.copy(src, dest)
    replace_projname_for_files(dest,
                               rules.project_rule.lower_name,
                               rules.project_rule.upper_name)

    print('[*] Done setting up build scripts')


def setup_clang_format_file(rule_file):
    print('[*] Setting up clang-format file')

    f = '.clang-format'

    shutil.copy(path.join(path.dirname(path.abspath(__file__)), 'scaffolds', f),
                path.join(path.dirname(rule_file), f))

    print('[*] Done setting up .clang-format')


def setup_clang_tidy_file(rule_file):
    print('[*] Setting up clang-tidy file')

    f = '.clang-tidy'

    shutil.copy(path.join(path.dirname(path.abspath(__file__)), 'scaffolds', f),
                path.join(path.dirname(rule_file), f))

    print('[*] Done setting up .clang-tidy')

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
    setup_clang_tidy_file(args.rule_file)
