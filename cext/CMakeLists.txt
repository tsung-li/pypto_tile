# Copyright (c) 2026 PYPTO Contributors
# SPDX-License-Identifier: MIT

# Find Python
find_package(Python COMPONENTS Interpreter Development REQUIRED)

# Find nanobind
execute_process(
  COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
  OUTPUT_VARIABLE nanobind_DIR
  OUTPUT_STRIP_TRAILING_WHITESPACE
)
find_package(nanobind CONFIG REQUIRED)

nanobind_add_module(
    _cext
    src/module.cpp
)
