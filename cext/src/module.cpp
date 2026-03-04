/* Copyright (c) 2026 PYPTO Contributors
 * SPDX-License-Identifier: MIT
 */

#include <nanobind/nanobind.h>

namespace nb = nanobind;

NB_MODULE(_cext, m) { m.doc() = "pypto.tile C extension module"; }
