# ----------------------------------------------------------------------
# |
# |  CodeCoverageExecutor.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-04-25 15:31:24
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019-20
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the CodeCoverageExecutor object"""

import json
import os
import shutil

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import FileSystem
from CommonEnvironment import Interface
from CommonEnvironment import Process
from CommonEnvironment.Shell.All import CurrentShell

from CppCommon.CodeCoverageExecutor import (
    CodeCoverageExecutor as CodeCoverageExecutorBase,
)

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class CodeCoverageExecutor(CodeCoverageExecutorBase):
    """Extracts code coverage using Clang tools"""

    # ----------------------------------------------------------------------
    # |  Properties
    DefaultFileName                         = Interface.DerivedProperty("lcov.info")
    Units                                   = Interface.DerivedProperty("lines")

    # ----------------------------------------------------------------------
    # |  Methods
    def __init__(self):
        self._coverage_filename             = None
        self._dirs                          = set()

    # ----------------------------------------------------------------------
    @Interface.override
    def PreprocessBinary(self, binary_filename, output_stream):
        self._dirs.add(os.path.dirname(binary_filename))
        return 0

    # ----------------------------------------------------------------------
    @Interface.override
    def StartCoverage(self, coverage_filename, output_stream):
        # Preserve the final coverage filename
        self._coverage_filename = coverage_filename
        return 0

    # ----------------------------------------------------------------------
    @Interface.override
    def StopCoverage(self, output_stream):
        if not self._dirs:
            return 0

        # Move coverage data to this dir
        output_dir = os.path.dirname(self._coverage_filename)

        for filename in FileSystem.WalkFiles(
            output_dir,
            include_file_extensions=[".gcda"],
        ):
            dest_filename = os.path.join(output_dir, os.path.basename(filename))
            if dest_filename == filename:
                continue

            if not os.path.isfile(dest_filename):
                shutil.copyfile(filename, dest_filename)

        return Process.Execute(
            '{script} Lcov {dirs} "/output_dir={output}"'.format(
                script=CurrentShell.CreateScriptName("ExtractCoverageInfo"),
                dirs=" ".join(['"/bin_dir={}"'.format(dir) for dir in self._dirs]),
                output=output_dir,
            ),
            output_stream,
        )

    # ----------------------------------------------------------------------
    @Interface.override
    def ExtractCoverageInfo(
        self,
        coverage_filename,
        binary_filename,
        includes,
        excludes,
        output_stream,
    ):

        # This is a hack. The names extracted are mangled while the names provided
        # in includes and excludes are in the glob format. Split the glob and then
        # determine matches by checking to see if each component is in the mangled name.
        # There is a lot that could go wrong with this, but hopefully it is good enough.

        # ----------------------------------------------------------------------
        def ProcessFilter(value):
            return [part for part in value.split("::") if part != "*"]

        # ----------------------------------------------------------------------
        def Matches(value, parts):
            for part in parts:
                if part not in value:
                    return False

            return True

        # ----------------------------------------------------------------------

        if excludes:
            excludes = [ProcessFilter(exclude) for exclude in excludes]
            excludes_func = lambda method_name: any(
                Matches(method_name, exclude) for exclude in excludes
            )
        else:
            excludes_func = lambda method_name: False

        if includes:
            includes = [ProcessFilter(include) for include in includes]
            includes_func = lambda method_name: any(
                Matches(method_name, include) for include in includes
            )
        else:
            includes_func = lambda method_name: True

        # ----------------------------------------------------------------------
        def ShouldInclude(method_name):
            return not excludes_func(method_name) and includes_func(method_name)

        # ----------------------------------------------------------------------

        # grcov will parse every file in the directory which isn't what we want here. Move the coverage
        # files for this binary to a temp dir, parse that dir, and then remove it.
        temp_directory = CurrentShell.CreateTempDirectory()

        with CallOnExit(lambda: FileSystem.RemoveTree(temp_directory)):
            # ----------------------------------------------------------------------
            def GetCoverageFilename(ext):
                dirname, basename = os.path.split(binary_filename)
                basename = os.path.splitext(basename)[0]

                for item in os.listdir(dirname):
                    fullpath = os.path.join(dirname, item)
                    if not os.path.isfile(fullpath):
                        continue

                    this_basename, this_ext = os.path.splitext(item)
                    if this_ext == ext and this_basename.startswith(basename):
                        return fullpath

                return None

            # ----------------------------------------------------------------------

            gcno_filename = GetCoverageFilename(".gcno")
            assert gcno_filename and os.path.isfile(gcno_filename), (binary_filename, gcno_filename)

            shutil.copyfile(
                gcno_filename,
                os.path.join(temp_directory, os.path.basename(gcno_filename)),
            )

            gcda_filename = GetCoverageFilename(".gcda")
            assert gcda_filename and os.path.isfile(gcda_filename), (binary_filename, gcda_filename)

            shutil.copyfile(
                gcda_filename,
                os.path.join(temp_directory, os.path.basename(gcda_filename)),
            )

            # Convert the content
            result = Process.Execute(
                '{} Lcov "/bin_dir={}" /type=ade'.format(
                    CurrentShell.CreateScriptName("ExtractCoverageInfo"),
                    temp_directory,
                ),
                output_stream,
            )

            if result != 0:
                return result

            coverage_filename = os.path.join(temp_directory, "lcov.info")
            assert os.path.isfile(coverage_filename), coverage_filename

            # Parse the file
            covered = 0
            not_covered = 0

            with open(coverage_filename) as f:
                for line in f.readlines():
                    content = json.loads(line)

                    if "method" not in content:
                        continue

                    content = content["method"]

                    if (
                        "name" not in content
                        or "total_covered" not in content
                        or "total_uncovered" not in content
                    ):
                        continue

                    if not ShouldInclude(content["name"]):
                        continue

                    covered += content["total_covered"]
                    not_covered += content["total_uncovered"]

            return covered, not_covered
