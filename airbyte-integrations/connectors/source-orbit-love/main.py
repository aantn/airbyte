#
# Copyright (c) 2021 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from source_orbit_love import SourceOrbitLove

if __name__ == "__main__":
    source = SourceOrbitLove()
    launch(source, sys.argv[1:])
