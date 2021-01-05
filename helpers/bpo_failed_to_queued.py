#!/usr/bin/env python3
# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
""" Change status of all failed packages and images back to queued. """
import argparse
import os
import sys

# Add topdir to import path
topdir = os.path.realpath(os.path.join(os.path.dirname(__file__) + "/.."))
sys.path.insert(0, topdir)

# Use "noqa" to ignore "E402 module level import not at top of file"
import bpo.db  # noqa
import bpo.config.args  # noqa
import bpo.config.const.args  # noqa


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--db-path", help="path to sqlite3 database",
                        default=bpo.config.const.args.db_path)
    return parser.parse_args()


def init_db(db_path):
    sys.argv = ["bpo.py", "-d", db_path, "local"]
    bpo.config.args.init()
    bpo.db.init()


def confirm(statement):
    print(statement)
    answer = input("Are you sure? [y/N] ")
    if answer != "y":
        print("Not answered with 'y', aborting!")
        sys.exit(1)


def get_failed_packages(session):
    return session.query(bpo.db.Package).\
        filter_by(status=bpo.db.PackageStatus.failed).\
        all()


def get_failed_images(session):
    return session.query(bpo.db.Image).\
        filter_by(status=bpo.db.ImageStatus.failed).\
        all()


def list_failed(packages, images):
    if packages:
        print(f"Failed packages ({len(packages)}):")
        for package in packages:
            print(f"* {package.branch}/{package.arch}/{package.pkgname}-"
                  f"{package.version}")
    if images:
        print(f"Failed images ({len(images)}):")
        for image in images:
            print(f"* {image.branch}:{image.device}:{image.ui}")


def change_to_queued(session, packages, images):
    for package in packages:
        package.status = bpo.db.PackageStatus.queued
        session.merge(package)

    for image in images:
        image.status = bpo.db.ImageStatus.queued
        session.merge(image)

    session.commit()


def main():
    args = parse_arguments()
    if not os.path.exists(args.db_path):
        print("ERROR: could not find database: " + args.db_path)
        sys.exit(1)

    init_db(args.db_path)
    session = bpo.db.session()
    packages = get_failed_packages(session)
    images = get_failed_images(session)

    if not images and not packages:
        print("No failed images or packages found.")
        sys.exit(0)

    list_failed(packages, images)
    print()

    confirm("Changing status from 'failed' to 'queued'.")
    change_to_queued(session, packages, images)
    print("Done!")


if __name__ == "__main__":
    sys.exit(main())
