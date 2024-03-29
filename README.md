anvil is an assistant for your cmake to bootstrap a new C++ project and to manage its build workflow.

## Overview

CMake is the de-facto build system for C++ projects and it becomes more dominant in the community.

However, CMake is not friendly to novice to get started, and even for users who use cmake frequently, it is still kinda tedious to setup necessary cmake files for a new project; let alone using cmake to manage your dependencies.

anvil tries to improve your user experience in using CMake by providing features like:

- bootstrapping a new project out of a configured template.
- an out-of-box lightweight dependency manager for medium-sized projects.
- built-in building scripts for various platforms

## Installation

### Prerequisites

- OS: any OS that meets following requirements
- Python 3
- CMake 3.14 or higher (our built-in dependency manager relies on fetch-content module)

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
anvil init "path/to/your/project_rules.toml"
```

Anvil would now create folders and whatever requested for you.

### Configure generation & build

You can either use CMake commands directly to generate build files and then build your project; or you can use `build.py` which provides simpler commands for generating and building.

Run `python3 build.py --help` for details.

### Using Dependency Manager

We use [CPM.cmake](https://github.com/TheLartians/CPM.cmake) as our default dependency management.
