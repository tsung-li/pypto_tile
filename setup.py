# Copyright (c) 2026 PYPTO Contributors
# SPDX-License-Identifier: MIT
import shutil

from setuptools import setup
from setuptools.command.build_ext import build_ext
from setuptools.command.bdist_wheel import bdist_wheel
from setuptools.extension import Extension
import glob
import os


project_root = os.path.dirname(os.path.abspath(__file__))


class BuildExtWithCmake(build_ext):
    user_options = build_ext.user_options + []

    def initialize_options(self):
        super().initialize_options()

    def finalize_options(self):
        super().finalize_options()

    def _make(self, build_dir: str, build_type: str, parallel: int):
        self.spawn(["make", "-C", build_dir, "-j", str(parallel)])

    def _cmake(self, build_dir: str, build_type: str, dlpack_path: str):
        cmake_cmd = [
            "cmake",
            "-B",
            build_dir,
            project_root,
            f"-DDLPACK_PATH={dlpack_path}",
            f"-DCMAKE_BUILD_TYPE={build_type}",
            "-DCMAKE_POLICY_VERSION_MINIMUM=3.5",
        ]
        self.spawn(cmake_cmd)  # type: ignore

    def run(self):
        build_dir = os.getenv("PYPTO_TILE_CEXT_BUILD_DIR")
        if build_dir is None or build_dir == "":
            if self.editable_mode:
                build_dir = os.path.join(project_root, "build")
            else:
                build_dir = self.build_temp

        build_type = "Debug" if self.debug else "Release"
        dlpack_path = os.getenv("PYPTO_TILE_CMAKE_DLPACK_PATH", "")
        parallel = 1 if self.parallel is None else self.parallel
        self._cmake(build_dir, build_type, dlpack_path)
        self._make(build_dir, build_type, parallel)

        for ext in self.extensions:
            src_dir = _get_csrc_dir(ext.name)
            # Find the built library file (nanobind uses platform-specific naming like libcext.cpython-311-*.so)
            # We need to match both the .so extension and the platform-specific suffix
            base_name = _get_build_lib_filename(ext.name).replace(
                ".so", ""
            )  # Get "libcext"
            search_pattern = os.path.join(build_dir, src_dir, f"{base_name}*.so")
            matches = glob.glob(search_pattern)
            if not matches:
                raise RuntimeError(
                    f"Could not find built library matching: {search_pattern}"
                )
            ext_build_path = matches[0]  # Use the first match
            ext_path = self.get_ext_fullpath(ext.name)
            # Create a symlink to the build directory if in editable mode, otherwise copy
            if self.editable_mode:
                if os.path.exists(ext_path):
                    os.remove(ext_path)
                os.symlink(ext_build_path, ext_path)
            else:
                shutil.copy2(ext_build_path, ext_path)


class BdistWheelWithDeps(bdist_wheel):
    user_options = bdist_wheel.user_options + []

    def initialize_options(self):
        super().initialize_options()

    def finalize_options(self):
        super().finalize_options()


def _get_csrc_dir(ext_name: str):
    prefix = "pypto.tile._"
    assert ext_name.startswith(prefix)
    return ext_name[len(prefix) :]


def _get_build_lib_filename(ext_name: str):
    name = ext_name.split(".")[-1]
    return f"{name}.so"


setup(
    ext_modules=[
        Extension("pypto.tile._cext", []),
    ],
    cmdclass=dict(build_ext=BuildExtWithCmake, bdist_wheel=BdistWheelWithDeps),
)
