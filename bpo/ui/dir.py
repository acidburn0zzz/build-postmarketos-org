# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later
import bpo.helpers.job


def write_readme_image(image, path):
    """ Generate a readme.html for one image directory (which contains one or
        more postmarketOS images for a specific branch:device:ui combination).
        The readme.html links to the job that built the image etc.

        :param image: bpo.db.Image object
        :param path: full path to the readme.html to be generated """
    template = bpo.ui.env.get_template("dir_readme_image.html")
    html = template.render(image=image,
                           job_link=bpo.helpers.job.get_link(image.job_id))

    with open(path, "w") as handle:
        handle.write(html)
