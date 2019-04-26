#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 0xCCCCCCCC

import os
import shutil
import toml

from os import path


_CMAKE_TEMPLATE = 'cmake_minimum_required(VERSION %s)\n'

_PROJECT_TEMPLATE = '''# Detect if being bundled via sub-directory.
if(NOT DEFINED PROJECT_NAME)
  set({cap_name}_NOT_SUBPROJECT ON)
endif()

project({name} CXX)

set_property(GLOBAL PROPERTY USE_FOLDERS ON)

if({cap_name}_NOT_SUBPROJECT)
  set(CMAKE_CXX_STANDARD {cxx_standard})
  set(CMAKE_CXX_STANDARD_REQUIRED ON)
  set(CMAKE_CXX_EXTENSIONS OFF)

  set(ROOT_DIR ${{CMAKE_SOURCE_DIR}})
  set(DEPS_SOURCE_DIR ${{ROOT_DIR}}/{dep_src_dir})
  set(DEPS_DEPLOY_DIR {dep_deploy_dir})
endif()

# Add options here.

set({cap_name}_DIR ${{CMAKE_CURRENT_SOURCE_DIR}})
set({cap_name}_DEPS_DIR ${{{cap_name}_DIR}}/deps)
set({cap_name}_CMAKE_DIR ${{{cap_name}_DIR}}/cmake)

include(${{{cap_name}_CMAKE_DIR}}/dependency_manager.cmake)
'''

_PCH_TEMPLATE = '''include(${{{cap_name}_CMAKE_DIR}}/cotire.cmake)
set({cap_name}_PCH_HEADER ${{{cap_name}_DIR}}/{pch_file})
'''

_COMPILER_MSVC_TEMPLATE = '''include(${{{cap_name}_CMAKE_DIR}}/compiler_msvc.cmake)
foreach(OUTPUTCONFIG_TYPE ${{CMAKE_CONFIGURATION_TYPES}})
  string(TOUPPER ${{OUTPUTCONFIG_TYPE}} OUTPUTCONFIG)
  set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_${{OUTPUTCONFIG}} ${{CMAKE_BINARY_DIR}}/${{OUTPUTCONFIG_TYPE}}/bin)
  set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY_${{OUTPUTCONFIG}} ${{CMAKE_BINARY_DIR}}/${{OUTPUTCONFIG_TYPE}}/lib)
endforeach()
'''

_COMPILER_POSIX_TEMPLATE = '''include(${{{cap_name}_CMAKE_DIR}}/compiler_posix.cmake)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${{CMAKE_BINARY_DIR}}/bin)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${{CMAKE_BINARY_DIR}}/lib)
'''

_ADD_MAIN_MODULE_TEMPLATE = 'add_subdirectory({name})\n'

_MAIN_SRCS_TEMPLATE = '''set({name}_SRCS
)
'''

_MAIN_MULTI_SRCS_TEMPLATE = '''if(WIN32)
  list(APPEND {name}_SRCS
  )
elseif(UNIX)
  list(APPEND {name}_SRCS
  )
endif()
'''

_MAIN_HEADERS_TEMPLATE = '''set({name}_HEADERS
)
'''

_MAIN_MULTI_HEADERS_TEMPLATE = '''if(WIN32)
  list(APPEND {name}_HEADERS
  )
elseif(UNIX)
  list(APPEND {name}_HEADERS
  )
endif()
'''

_MAIN_PROPERTY_TEMPLATE = '''set({name}_FILES ${{{name}_HEADERS}} ${{{name}_SRCS}})

source_group("{name}" FILES ${{{name}_FILES}})

add_{type}({name} ${{{name}_FILES}})

apply_common_compile_properties_to_target({name})
'''

_MAIN_MSVC_STATIC_ANALYSIS_TEMPLATE = '''if(MSVC)
  enable_msvc_static_analysis_for_target({name})
endif()
'''

_MAIN_USE_PCH_TEMPLATE = '''set_target_properties({name} PROPERTIES
  COTIRE_CXX_PREFIX_HEADER_INIT "${{{cap_name}_PCH_HEADER}}"
)

cotire({name})
'''

_MAIN_TARGET_TEMPLATE = '''target_include_directories({name}
  PUBLIC ${{CMAKE_CURRENT_SOURCE_DIR}}/../
)

# Uncomment if you use them.
#target_compile_definitions({name}
#)

target_link_libraries({name}
)
'''


class CMakeRule:
    def __init__(self, data):
        self.min_ver = data['min_ver']


class ProjectRule:
    def __init__(self, data):
        self.name = data['name']
        self.upper_name = str.upper(self.name)
        self.deps_source_dir = data['deps_source_dir']
        self.deps_deploy_dir = data['deps_deploy_dir']
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


class Rules:
    def __init__(self, data):
        self.cmake_rule = CMakeRule(data['cmake'])
        self.project_rule = ProjectRule(data['project'])
        self.pch_rule = PCHRule(data['precompiled_header'])
        self.platform_support_rule = PlatformSupportRule(data['platform_support'])
        self.main_module_rule = MainModuleRule(data['main_module'])


def generate_cmake_ver_part(rules):
    return _CMAKE_TEMPLATE % rules.cmake_rule.min_ver


def generate_project_part(rules):
    return _PROJECT_TEMPLATE.format(cap_name=rules.project_rule.upper_name,
                                    name=rules.project_rule.name,
                                    dep_src_dir=rules.project_rule.deps_source_dir,
                                    dep_deploy_dir=rules.project_rule.deps_deploy_dir,
                                    cxx_standard=rules.project_rule.cxx_standard)


def generate_pch_part(rules):
    if rules.pch_rule.enabled:
        return _PCH_TEMPLATE.format(cap_name=rules.project_rule.upper_name,
                                    pch_file=rules.pch_rule.pch_file)
    else:
        return ''


def indent_lines(s, indent_size):
    return str.join('\n', map(lambda ln: ' ' * indent_size + ln if ln != '' else '',
                              str.splitlines(s)))


def generate_compiler_part(rules):
    text = '#Compiler and output configurations.\n'

    msvc = ''
    posix = ''
    if rules.platform_support_rule.support_windows:
        msvc = _COMPILER_MSVC_TEMPLATE.format(cap_name=rules.project_rule.upper_name)
    if rules.platform_support_rule.support_posix:
        posix = _COMPILER_POSIX_TEMPLATE.format(cap_name=rules.project_rule.upper_name)

    if msvc != '' and posix != '':
        text += 'if(MSVC)\n'
        text += indent_lines(msvc, 2)
        text += '\nelse()\n'
        text += indent_lines(posix, 2)
        text += '\nendif()\n'
    else:
        text += msvc if msvc != '' else posix

    return text


def generate_add_main_module_part(rules):
    return _ADD_MAIN_MODULE_TEMPLATE.format(name=rules.main_module_rule.name)


def generate_root_cmake_file(rules):
    print('[*] Generating root CMakeLists.txt...')

    with open('CMakeLists.txt', 'w') as f:
        f.write(generate_cmake_ver_part(rules))
        f.write('\n')

        f.write(generate_project_part(rules))
        f.write('\n')

        f.write(generate_pch_part(rules))
        f.write('\n')

        f.write(generate_compiler_part(rules))
        f.write('\n')

        f.write(generate_add_main_module_part(rules))

    print('[*] Done generating root CMakeLists.txt...')


def setup_cmake_module_folder(rules):
    print('[*] Setting up cmake modules')

    dest_dir = 'cmake'
    if not path.exists(dest_dir):
        os.mkdir(dest_dir)

    module_dir = path.join(path.dirname(path.abspath(__file__)), 'scaffolds', 'cmake_modules')

    if rules.platform_support_rule.support_posix:
        file = 'compiler_posix.cmake'
        shutil.copy(path.join(module_dir, file), path.join(dest_dir, file))

    if rules.platform_support_rule.support_windows:
        file = 'compiler_msvc.cmake'
        shutil.copy(path.join(module_dir, file), path.join(dest_dir, file))

    if rules.pch_rule.enabled:
        file = 'cotire.cmake'
        shutil.copy(path.join(module_dir, file), path.join(dest_dir, file))

    special_files = ('compiler_posix.cmake', 'compiler_msvc.cmake', 'cotire.cmake',)
    normal_files = filter(lambda name: name not in special_files, os.listdir(module_dir))
    for file in normal_files:
        shutil.copy(path.join(module_dir, file), path.join(dest_dir, file))

    print('[*] Done setting up cmake modules')


def setup_pch_files(rules):
    if not rules.pch_rule.enabled:
        return

    pch_folder = path.dirname(rules.pch_rule.pch_file)
    if not path.exists(pch_folder):
        os.makedirs(pch_folder)

    pch_src_dir = path.join(path.dirname(path.abspath(__file__)), 'scaffolds', 'pch')

    shutil.copy(path.join(pch_src_dir, 'precompile.h'), rules.pch_rule.pch_file)
    shutil.copy(path.join(pch_src_dir, 'precompile.cpp'), path.join(pch_folder, 'precompile.cpp'))


def generate_main_module_cmake_file(rules):
    main_dir = rules.main_module_rule.name

    if not path.exists(main_dir):
        os.mkdir(main_dir)

    with open(path.join(main_dir, 'CMakeLists.txt'), 'w') as f:
        f.write('\n')

        f.write(_MAIN_SRCS_TEMPLATE.format(name=rules.main_module_rule.name))
        f.write('\n')

        if rules.platform_support_rule.support_windows and rules.platform_support_rule.support_posix:
            f.write(_MAIN_MULTI_SRCS_TEMPLATE.format(name=rules.main_module_rule.name))
            f.write('\n')

        f.write(_MAIN_HEADERS_TEMPLATE.format(name=rules.main_module_rule.name))
        f.write('\n')

        if rules.platform_support_rule.support_windows and rules.platform_support_rule.support_posix:
            f.write(_MAIN_MULTI_HEADERS_TEMPLATE.format(name=rules.main_module_rule.name))
            f.write('\n')

        f.write(_MAIN_PROPERTY_TEMPLATE.format(name=rules.main_module_rule.name,
                                               type=rules.main_module_rule.type))
        f.write('\n')

        if rules.main_module_rule.use_msvc_sa:
            f.write(_MAIN_MSVC_STATIC_ANALYSIS_TEMPLATE.format(name=rules.main_module_rule.name))
            f.write('\n')

        if rules.main_module_rule.use_pch:
            f.write(_MAIN_USE_PCH_TEMPLATE.format(name=rules.main_module_rule.name,
                                                  cap_name=str.upper(rules.main_module_rule.name)))
            f.write('\n')

        f.write(_MAIN_TARGET_TEMPLATE.format(name=rules.main_module_rule.name))


def run_init_job(args):
    data = toml.load(args.rule_file)
    rules = Rules(data)
    generate_root_cmake_file(rules)
    setup_cmake_module_folder(rules)
    setup_pch_files(rules)
    generate_main_module_cmake_file(rules)
