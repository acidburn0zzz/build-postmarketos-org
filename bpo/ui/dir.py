# Copyright 2021 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
import fnmatch
import glob
import logging
import os

import bpo.helpers.job
import bpo.images


def write_header(path, title):
    """ Write a header.html, as our nginx configuration expects it to exist for
        each directory.
        :param path: full path to where it will get saved
        :title: what to put in the <title> tag """
    template = bpo.ui.env.get_template("dir_header.html")
    html = template.render(title=title)

    with open(path, "w") as handle:
        handle.write(html)


def write_readme(path):
    """ Readme.html, as expected by our nginx config. Basically the footer of
        the page. Use for everything leading up to the resulting image dir, we
        have write_readme_image() for that. """
    template = bpo.ui.env.get_template("dir_readme.html")
    html = template.render()

    with open(path, "w") as handle:
        handle.write(html)


def write_readme_image(path, image):
    """ Generate a readme.html for one image directory (which contains one or
        more postmarketOS images for a specific branch:device:ui combination).
        The readme.html links to the job that built the image etc.

        :param path: full path to the readme.html to be generated
        :param image: bpo.db.Image object """

    template = bpo.ui.env.get_template("dir_readme_image.html")
    html = template.render(image=image,
                           job_link=bpo.helpers.job.get_link(image.job_id))

    with open(path, "w") as handle:
        handle.write(html)


def is_outdated(path, template):
    """ Check if a generated HTML file needs to be updated, either because it
        does not exist, or because the template has a more recent modified
        date.
        :param template: file name of a template, e.g. dir_header.html
        :returns: True if it is outdated, False if up-to-date
    """
    if not os.path.exists(path):
        return True

    path_template = f"{bpo.config.const.top_dir}/data/templates/{template}"
    return os.path.getmtime(path) <= os.path.getmtime(path_template)


def write_header_if_outdated(path):
    path += "header.html"
    template = "dir_header.html"
    if not is_outdated(path, template):
        return

    # Generate title
    relpath = os.path.relpath(path, bpo.config.args.images_path)
    relpath_dir = os.path.dirname(relpath)
    title = relpath_dir
    if title:
        title += " - "
    title += "images.postmarketos.org"

    logging.info(f"Generate from {template}: {path} (title: {title})")
    write_header(path, title)


def write_readme_if_outdated(path):
    """ :param path: with trailing slash to some directory in images_path """
    path_file = f"{path}readme.html"

    # Dir contains image files
    pattern_image = f"{bpo.config.args.images_path}/*/*/*/*/"
    if fnmatch.fnmatch(path, pattern_image):
        template = "dir_readme_image.html"
        if is_outdated(path_file, template):
            image = bpo.images.db_obj_from_path(os.path.dirname(path))
            logging.info(f"Generate from {template}: {path_file}")
            write_readme_image(path_file, image)
        return

    # Parent directory
    template = "dir_readme.html"
    if is_outdated(path_file, template):
        logging.info(f"Generate from {template}: {path_file}")
        write_readme(path_file)


def write_all():
    """ For each directory in the images dir (recursively), write the HTML
        files if they are missing, or the templates are newer. """

    for path in glob.iglob(f"{bpo.config.args.images_path}/**/",
                           recursive=True):
        write_header_if_outdated(path)
        write_readme_if_outdated(path)
