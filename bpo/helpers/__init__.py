# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later


class ThisExceptionIsExpectedAndCanBeIgnored(Exception):
    """ Expected exception from the testsuite, that sometimes shows up on the
        terminal (multithreading, yay) while running the testsuite. It would be
        better to hide it, but I could not find a feasible way in a reasonable
        amount of time. """
    pass
