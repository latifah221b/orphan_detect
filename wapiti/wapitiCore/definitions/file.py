#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of the Wapiti project (https://wapiti-scanner.github.io)
# Copyright (C) 2021-2022 Nicolas Surribas
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
TYPE = "vulnerability"

NAME = "Path Traversal"
SHORT_NAME = NAME

WSTG_CODE = ["WSTG-ATHZ-01"]

DESCRIPTION = (
    "This attack is known as Path or Directory Traversal."
) + " " + (
    "Its aim is the access to files and directories that are stored outside the web root folder."
) + " " + (
    "The attacker tries to explore the directories stored in the web server."
) + " " + (
    "The attacker uses some techniques, for instance, the manipulation of variables that reference files with "
    "'dot-dot-slash (../)' sequences and its variations to move up to root directory to navigate through "
    "the file system."
)

SOLUTION = (
    "Prefer working without user input when using file system calls."
) + " " + (
    "Use indexes rather than actual portions of file names when templating or using language files "
    "(eg: value 5 from the user submission = Czechoslovakian, rather than expecting the user to return "
    "'Czechoslovakian')."
) + " " + (
    "Ensure the user cannot supply all parts of the path - surround it with your path code."
) + " " + (
    "Validate the user's input by only accepting known good - do not sanitize the data."
) + " " + (
    "Use chrooted jails and code access policies to restrict where the files can be obtained or saved to."
)

REFERENCES = [
    {
        "title": "OWASP: Path Traversal",
        "url": (
            "https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/"
            "05-Authorization_Testing/01-Testing_Directory_Traversal_File_Include"
        )
    },
    {
        "title": "Acunetix: What is a Directory Traversal attack?",
        "url": "https://www.acunetix.com/websitesecurity/directory-traversal/"
    },
    {
        "title": "CWE-22: Improper Limitation of a Pathname to a Restricted Directory ('Path Traversal')",
        "url": "https://cwe.mitre.org/data/definitions/22.html"
    },
]
