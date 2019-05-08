anvil is an assistant for your cmake to bootstrap a new C++ project and to manage its build workflow.

## Overview

CMake is the de-facto build system for C++ projects and it becomes more dominant in the community.

However, CMake is not friendly to novice to get started, and even for users who use cmake frequently, it is still kinda tedious to setup necessary cmake files for a new project; let alone using cmake to manage your dependencies.

anvil tries to improve your user experience in using CMake by providing features like:

- bootstrapping a new project out of a configured template.
- a built-in lightweight dependency manager for medium-sized projects.
- configurable generation & build

## Installation

### Prerequisites

- OS: any OS that meets following requirements
- Python 3
- CMake 3.11 or higher (our built-in dependency manager relies on fetch-content module)

### Steps

1. Clone the project and `cd` into the directory

2. Run `pip install -r requirements.txt`
  and to make sure `pip` here referes to the Python 3 version.

3. Make sure `anvil/launcher/anvil.bat` accessible in your PATH on Windows; and

   make sure `anvil/launcher/anvil` accessible in your PATH on other platforms.

4. Run `anvil --help` to verify the installation.


## Quick Start

### Bootstrap a Project

Create the directory `Demo` for your new project and copy file `anvil/scaffolds/project_rules.toml` to somewhere (it is ok to place it into the `Demo` directory)

Edit the `project_rules.toml` and make it meet your requirements.

Then:

```shell
cd Demo
anvil init "path-to-your-project-rules.toml"
```

Anvil would now create folders and files for you; and a copy of the used `project_rules.toml` alone with a `config.toml` will be placed into the `.anvil` folder under your project folder.

### Configure generation & build

Edit `.anvil/configs.toml` to make it meet your requirements.

This file is called configuration set, and contains different configuration; each contains more than one _configuration targets_ and _build modes_.

The file contains brief description and example templates and tries to make it self-explained.

The command for generating is `anvil gen configuration[.target]`

If `target` is empty, then `.target` can be omitted.

```shell
anvil gen msvc-2019
anvil gen ninja-clang.Debug
```

The command for building is `anvil build configuration[.target] [--mode=] [--no-gen]`

```shell
anvil build msvc-2019 --mode=Debug
anvil build ninja-clang.Debug --no-gen
```

If build mode is empty, then `--mode=` can be omitted.

`build` will first `gen` the project, use `--no-gen` to suppress it.

### Using Dependency Manager

After setting up a project via anvil, you have deployed anvil's dependency manager into your project, which is located at `project/cmake/dependency_manager.cmake`

If one of your module relies on `Catch2`, just add following into your module's `CMakeLists.txt`

```cmake
declare_dep_module(Catch2
  VERSION         2.5.0
  GIT_REPOSITORY  https://github.com/catchorg/Catch2.git
  GIT_TAG         v2.5.0
)

#...

target_link_libraries(demo
  PRIVATE
    Catch2
)
```

Then the specified revision of Catch2 will be downloaded and being added to your project during generation.

Our built-in dependency manager module chooses source-code dependency over binary dependency; and this dependency model gets you rid of tricky ABI-compability issues.

All deps source code are archived at `project/build/deps` by default, and these local copies will be reused whenever possible (if `VERSION` remains the same) to prevent unnecessary downloading when you switch between generators.