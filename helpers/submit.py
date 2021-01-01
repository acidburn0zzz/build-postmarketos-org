#!/usr/bin/env python3
# Copyright 2020 Martijn Braam, Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
# Submit data to the bpo api:
# bpo runs this script in a job service (sourcehut builds, local) to return the
# result (built package etc.) to the bpo server.

import json
import os
import requests

# Require environment vars
for key in ["BPO_API_ENDPOINT",
            "BPO_API_HOST",
            "BPO_ARCH",
            "BPO_BRANCH",
            "BPO_JOB_ID",
            "BPO_JOB_NAME",
            "BPO_PAYLOAD_FILES",    # one file per line
            "BPO_PAYLOAD_IS_JSON",  # set to "1" to enable
            "BPO_PKGNAME",
            "BPO_TOKEN_FILE",
            "BPO_VERSION",          # $pkgver-r$pkgrel
            ]:
    if key not in os.environ:
        print("ERROR: missing environment variable: " + key)
        exit(1)

# Parse and check files
files = os.environ["BPO_PAYLOAD_FILES"].split("\n")
for path in files:
    if not os.path.exists(path):
        print("ERROR: file not found: " + path)
        exit(1)

# Load token
with open(os.path.expanduser(os.environ["BPO_TOKEN_FILE"]),
          encoding="utf-8") as handle:
    token = handle.read().strip()

# Load other env vars
url = (os.environ["BPO_API_HOST"] + "/api/job-callback/" +
       os.environ["BPO_API_ENDPOINT"])
is_json = (os.environ["BPO_PAYLOAD_IS_JSON"] == "1")

# Prepare HTTP headers
headers = {"X-BPO-Arch": os.environ["BPO_ARCH"],
           "X-BPO-Branch": os.environ["BPO_BRANCH"],
           "X-BPO-Job-Id": os.environ["BPO_JOB_ID"],
           "X-BPO-Job-Name": os.environ["BPO_JOB_NAME"],
           "X-BPO-Pkgname": os.environ["BPO_PKGNAME"],
           "X-BPO-Token": token,
           "X-BPO-Version": os.environ["BPO_VERSION"]}

# The server may take long to answer (#49). Hack for the testsuite until this
# is resolved: set a timeout and ignore the ReadTimeout exception
timeout = None
if "BPO_TIMEOUT" in os.environ:
    timeout = float(os.environ["BPO_TIMEOUT"])

# Submit JSON
if is_json:
    if len(files) > 1:
        print("ERROR: json mode doesn't support multiple input files")
        exit(1)

    # Send contents of file as HTTP POST with json payload
    with open(files[0], encoding="utf-8") as handle:
        data = handle.read()
    data = json.loads(data)

    print("Sending JSON to: " + url)
    try:
        response = requests.post(url, json=data, headers=headers,
                                 timeout=timeout)
    except requests.exceptions.ReadTimeout:
        if "BPO_TIMEOUT_IGNORE" in os.environ:
            print("hack for testsuite: ignore timeout")
            exit(0)
        raise

else:  # Submit blobs
    blobs = []
    for path in files:
        print("Appending: " + path)
        filename = os.path.basename(path)
        # Send contents of file as HTTP POST with multipart/formdata payload
        blobs.append(("file[]", (filename,
                                 open(path, "rb"),
                                 "application/octet-stream")))

    print("Uploading to: " + url)
    try:
        response = requests.post(url, files=blobs, headers=headers,
                                 timeout=timeout)
    except requests.exceptions.ReadTimeout:
        if "BPO_TIMEOUT_IGNORE" in os.environ:
            print("hack for testsuite: ignore timeout")
            exit(0)
        raise

if response.status_code > 399:
    print("Error occurred:")
    print(response.content.decode())
    exit(1)
else:
    print(response.content.decode())
