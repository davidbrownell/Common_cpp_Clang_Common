# ----------------------------------------------------------------------
# |
# |  _custom_data.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-04-25 12:05:15
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Custom data used by both Setup_custom.py and Activate_custom.py"""

import os

import CommonEnvironment
from CommonEnvironment.Shell.All import CurrentShell

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

if CurrentShell.CategoryName == "Windows":
    _CUSTOM_DATA                            = [
        (
            "grcov - 0.4.3",
            "cf997417a8cd05d043eccdb71c2a7e76aafc3e03da1a439c8460125c25a9f483",
            [
                "Tools",
                "grcov",
                "v0.4.3",
                "Windows",
            ],
        ),
    ]
elif CurrentShell.CategoryName == "Linux":
    _CUSTOM_DATA                            = [
        (
            "grcov - 0.4.3",
            "8b68acb4e5467943aec3e1ec9472876c8f8544d00b489422a3a2d9895c58f0d1",
            [
                "Tools",
                "grcov",
                "v0.4.3",
                "Linux",
            ],
        ),
    ]
else:
    raise Exception("This repository has not been configured for this operating system")
