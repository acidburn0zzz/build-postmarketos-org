#!/usr/bin/env python3
# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Simple tool to set and get package status (#44) """
import argparse
import os
import sys

# Add topdir to import path
topdir = os.path.realpath(os.path.join(os.path.dirname(__file__) + "/.."))
sys.path.insert(0, topdir)

# Use "noqa" to ignore "E402 module level import not at top of file"
import bpo.db  # noqa
import bpo.config.args  # noqa


def status_choices():
    ret = []
    for status in bpo.db.PackageStatus:
        ret += [status.name]
    return sorted(ret)


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("pkgnames", nargs="*", help="relevant package name"
                        " (default: all)", metavar="pkgname")
    parser.add_argument("-a", "--arch", default="x86_64",
                        help="package architecture (default: x86_64)")
    parser.add_argument("-b", "--branch", default="master",
                        help="pmaports.git branch (default: master)")
    parser.add_argument("-d", "--db-path", help="path to sqlite3 database",
                        default=bpo.config.args.db_path)
    parser.add_argument("-f", help="when not specifying any pkgnames, instead"
                        " of considering all packages, only look at those with"
                        " a certain status", choices=status_choices(),
                        dest="filter_status")

    # Get or set
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-g", help="get current status value", dest="get",
                       action="store_true")
    group.add_argument("-s", help="set new status value", dest="status",
                       choices=status_choices())

    return parser.parse_args()


def get_all_pkgnames(session, arch, branch, status):
    if status:
        status = bpo.db.PackageStatus[status]
        packages = session.query(bpo.db.Package).filter_by(arch=arch,
                                                           branch=branch,
                                                           status=status)
    else:
        packages = session.query(bpo.db.Package).filter_by(arch=arch,
                                                           branch=branch)

    ret = []
    for package in packages:
        ret += [package.pkgname]
    return sorted(ret)


def confirm(statement):
    print(statement)
    answer = input("Are you sure? [y/N] ")
    if answer != "y":
        print("Not answered with 'y', aborting!")
        sys.exit(1)


def set_status(session, pkgnames, arch, branch, status):
    confirm("Will change status to '" + status + "' for the following"
            " packages: " + str(pkgnames))

    status = bpo.db.PackageStatus[status]
    for pkgname in pkgnames:
        package = bpo.db.get_package(session, pkgname, arch, branch)
        bpo.db.set_package_status(session, package, status)

    print("done!")
    print()


def get_status(session, pkgnames, arch, branch):
    format_str = "{:8s} | {}"
    print(format_str.format("status", "pkgname"))
    print("-" * 20)
    for pkgname in pkgnames:
        package = bpo.db.get_package(session, pkgname, arch, branch)
        print(format_str.format(package.status.name, package.pkgname))


def main():
    # Parse arguments
    args = parse_arguments()
    pkgnames = args.pkgnames
    arch = args.arch
    branch = args.branch
    if not os.path.exists(args.db_path):
        print("ERROR: could not find database: " + args.db_path)
        sys.exit(1)

    # Initialize db
    bpo.config.args.db_path = args.db_path
    bpo.db.init()
    session = bpo.db.session()

    if not pkgnames:
        pkgnames = get_all_pkgnames(session, arch, branch, args.filter_status)

    if args.status:
        set_status(session, pkgnames, arch, branch, args.status)

    get_status(session, pkgnames, arch, branch)


if __name__ == "__main__":
    sys.exit(main())
