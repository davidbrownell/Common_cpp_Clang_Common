# ----------------------------------------------------------------------
# |
# |  ExtractCoverageInfo.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-12-07 10:32:53
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019-22
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Extracts coverage information after test execution"""

import os
import sys
import textwrap

from collections import OrderedDict

import inflect as inflect_mod

import CommonEnvironment
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Process
from CommonEnvironment.Shell.All import CurrentShell
from CommonEnvironment.StreamDecorator import StreamDecorator

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
@CommandLine.EntryPoint()
@CommandLine.Constraints(
    bin_dir=CommandLine.DirectoryTypeInfo(
        arity="*",
    ),
    output_dir=CommandLine.DirectoryTypeInfo(
        ensure_exists=False,
        arity="?",
    ),
    output_filename=CommandLine.StringTypeInfo(
        arity="?",
    ),
    type=CommandLine.StringTypeInfo(
        arity="?",
    ),
    output_stream=None,
)
def Lcov(
    bin_dir=None,
    not_llvm=False,
    output_dir=None,
    output_filename="lcov.info",
    type=None,
    output_stream=sys.stdout,
    verbose=False,
):
    """Generates a LCOV file based on *.gcno files"""

    bin_dirs = bin_dir
    del bin_dir

    if not bin_dirs:
        bin_dirs.append(os.getcwd())

    if len(bin_dirs) > 1 and not output_dir:
        raise CommandLine.UsageException(
            "An 'output_dir' must be provided when multiple 'bin_dirs' are parsed",
        )

    if len(bin_dirs) == 1 and not output_dir:
        output_dir = bin_dirs[0]

    with StreamDecorator(output_stream).DoneManager(
        line_prefix="",
        prefix="\nResults: ",
        suffix="\n",
    ) as dm:
        output_filename = os.path.join(output_dir, output_filename)

        dm.stream.write("Creating '{}'...".format(output_filename))
        with dm.stream.DoneManager() as this_dm:
            FileSystem.MakeDirs(output_dir)

            command_line = 'grcov {dirs} -o "{output_filename}"{llvm}{type}'.format(
                dirs=" ".join(['"{}"'.format(dir) for dir in bin_dirs]),
                output_filename=output_filename,
                llvm="" if not_llvm else " --llvm",
                type="" if type is None else " -t {}".format(type),
            )

            if verbose:
                this_dm.stream.write(
                    textwrap.dedent(
                        """\
                        Command Line:
                            {}

                        """,
                    ).format(command_line),
                )

            this_dm.result = Process.Execute(command_line, this_dm.stream)
            if this_dm.result != 0:
                return this_dm.result

        return dm.result


# ----------------------------------------------------------------------
@CommandLine.EntryPoint()
@CommandLine.Constraints(
    bin_dir=CommandLine.DirectoryTypeInfo(
        arity="?",
    ),
    profraw_filename=CommandLine.StringTypeInfo(
        arity="?",
    ),
    profdata_filename=CommandLine.StringTypeInfo(
        arity="?",
    ),
    executable=CommandLine.FilenameTypeInfo(
        arity="*",
    ),
    source_dir=CommandLine.DirectoryTypeInfo(
        arity="*",
    ),
    output_filename=CommandLine.StringTypeInfo(
        arity="?",
    ),
    output_stream=None,
)
def Html(
    bin_dir=None,
    profraw_filename="default.profraw",
    profdata_filename="default.profdata",
    executable=None,
    source_dir=None,
    output_filename="code_coverage.html",
    force=False,
    no_sparse=False,
    output_stream=sys.stdout,
    verbose=False,
):
    """Generates a HTML file based on *.profdata files"""

    executables = executable
    del executable

    source_dirs = source_dir
    del source_dir

    if bin_dir is None:
        bin_dir = os.getcwd()

    with StreamDecorator(output_stream).DoneManager(
        line_prefix="",
        prefix="\nResults: ",
        suffix="\n",
    ) as dm:
        # Generate the profdata file (if necessary)
        profdata_filename = os.path.join(bin_dir, profdata_filename)

        if force or not os.path.isfile(profdata_filename):
            profraw_filename = os.path.join(bin_dir, profraw_filename)
            if not os.path.isfile(profraw_filename):
                raise CommandLine.UsageException(
                    "'{}' does not exist.".format(profraw_filename),
                )

            dm.stream.write("Creating '{}'...".format(profdata_filename))
            with dm.stream.DoneManager(
                suffix="\n",
            ) as this_dm:
                FileSystem.MakeDirs(os.path.dirname(profdata_filename))

                command_line = 'llvm-profdata merge {sparse} -o "{output_filename}" "{input_filename}"'.format(
                    sparse="" if no_sparse else "-sparse",
                    output_filename=profdata_filename,
                    input_filename=profraw_filename,
                )

                if verbose:
                    this_dm.stream.write(
                        textwrap.dedent(
                            """\
                            Command Line:
                                {}

                            """,
                        ).format(command_line),
                    )

                this_dm.result = Process.Execute(command_line, this_dm.stream)
                if this_dm.result != 0:
                    return this_dm.result

        # Generate the html
        output_filename = os.path.join(bin_dir, output_filename)

        dm.stream.write("Creating '{}'...".format(output_filename))
        with dm.stream.DoneManager(
            suffix="\n",
        ) as this_dm:
            if not executables:
                this_dm.stream.write("Finding executables...")
                with this_dm.stream.DoneManager(
                    done_suffix=lambda: "{} found".format(
                        inflect.no("executable", len(executables)),
                    ),
                ) as find_dm:
                    if CurrentShell.ExecutableExtension:
                        executables = list(
                            FileSystem.WalkFiles(
                                bin_dir,
                                include_file_extensions=[
                                    CurrentShell.ExecutableExtension
                                ],
                                recurse=False,
                            ),
                        )
                    else:
                        for filename in FileSystem.WalkFiles(
                            bin_dir,
                            recurse=False,
                        ):
                            if os.access(filename, os.X_OK):
                                executables.append(filename)

            FileSystem.MakeDirs(os.path.dirname(output_filename))

            command_line = 'llvm-cov show {executables} "-instr-profile={profdata}" -use-color --format html {sources} > "{output_filename}"'.format(
                executables=" ".join(
                    ['"{}"'.format(executable) for executable in executables],
                ),
                profdata=profdata_filename,
                sources=" ".join(
                    ['"{}"'.format(source_dir) for source_dir in source_dirs],
                ) if source_dirs else "",
                output_filename=output_filename,
            )

            if verbose:
                this_dm.stream.write(
                    textwrap.dedent(
                        """\
                        Command Line:
                            {}

                        """,
                    ).format(command_line),
                )

            this_dm.result = Process.Execute(command_line, this_dm.stream)
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
