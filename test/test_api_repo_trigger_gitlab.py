# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Test case idea:

* subprocess.run(bpo.py --local)
* have a pmpaports.git copy with testdata
    * how?
    * to run repo_missing, we don't need any files of the original repo.
        so we could just use complete fake one.
    * what we *do* need from the original repo, is the srht upload script.
    * so start with original repo, and copy everything we need from it.
* reset locally built repositories
* reset local database
* emulate gitlab's repo trigger api call to local bpo instance
* it should run the job that runs pmbootstrap repo_missing
* it should submit the result back to localhost
* dump database output and compare
"""
