# ----------------------------------------------------------------------
# |
# |  ClangCodeCoverageTestExecutor.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-05-01 23:16:30
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019-20
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the TestExecutor object"""

import os

import CommonEnvironment
from CommonEnvironment import Interface

from CppCommon.TestExecutorImpl import TestExecutorImpl
from CppClangCommon.CodeCoverageExecutor import CodeCoverageExecutor as ClangCodeCoverageExecutor

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@Interface.staticderived
class TestExecutor(TestExecutorImpl):
    # ----------------------------------------------------------------------
    # |  Properties
    Name                                    = Interface.DerivedProperty("ClangCodeCoverage")
    Description                             = Interface.DerivedProperty("Extracts code coverage information using Clang tools.")

    # ----------------------------------------------------------------------
    # |  Methods
    @staticmethod
    @Interface.override
    def IsSupportedCompiler(compiler):
        return compiler.Name in ["CMake"]

    # ----------------------------------------------------------------------
    _CodeCoverageExecutor                   = Interface.DerivedProperty(ClangCodeCoverageExecutor)
