# ----------------------------------------------------------------------
# |
# |  CreateLcovFile.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-04-25 16:12:03
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
import os
import sys

import CommonEnvironment
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Process
from CommonEnvironment.StreamDecorator import StreamDecorator

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

@CommandLine.EntryPoint(
)
@CommandLine.Constraints(
    bin_dir=CommandLine.DirectoryTypeInfo(
        arity="*",
    ),
    output_dir=CommandLine.DirectoryTypeInfo(
        ensure_exists=False,
        arity="?",
    ),
    type=CommandLine.StringTypeInfo(
        arity="?",
    ),
    output_stream=None,
)
def EntryPoint(
    bin_dir=None,
    not_llvm=False,
    output_dir=None,
    type=None,
    output_stream=sys.stdout,
):
    """Creates a lcov file from the results of a test run"""

    bin_dirs = bin_dir
    del bin_dir

    if not bin_dirs:
        bin_dirs.append(os.getcwd())

    if len(bin_dirs) > 1 and not output_dir:
        raise CommandLine.UsageException("An output_dir must be provided when multiple bin_dirs are parsed")
    elif len(bin_dirs) == 1 and not output_dir:
        output_dir = bin_dirs[0]

    with StreamDecorator(output_stream).DoneManager(
        line_prefix="",
        prefix="\nResults: ",
        suffix="\n",
    ) as dm:
        output_filename = os.path.join(output_dir, "lcov.info")

        dm.stream.write("Creating '{}'...".format(output_filename))
        with dm.stream.DoneManager() as this_dm:
            FileSystem.MakeDirs(output_dir)

            command_line = 'grcov {dirs} -o "{output_filename}"{llvm}{type}'.format(
                dirs=" ".join(['"{}"'.format(dir) for dir in bin_dirs]),
                output_filename=output_filename,
                llvm="" if not_llvm else " --llvm",
                type="" if type is None else " -t {}".format(type),
            )

            this_dm.result = Process.Execute(command_line, dm.stream)
            if this_dm.result != 0:
                return this_dm.result

        return dm.result


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(CommandLine.Main())
    except KeyboardInterrupt:
        pass
