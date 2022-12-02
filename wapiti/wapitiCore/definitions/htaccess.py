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

NAME = "Htaccess Bypass"
SHORT_NAME = NAME

WSTG_CODE = ["WSTG-CONF-06"]

DESCRIPTION = (
    "Htaccess files are used to restrict access to some files or HTTP method."
) + " " + (
    "In some case it may be possible to bypass this restriction and access the files."
)

SOLUTION = (
    "Make sure every HTTP method is forbidden if the credentials are bad."
)

REFERENCES = [
    {
        "title": "A common Apache .htaccess misconfiguration",
        "url": "http://blog.teusink.net/2009/07/common-apache-htaccess-misconfiguration.html"
    },
    {
        "title": "CWE-538: Insertion of Sensitive Information into Externally-Accessible File or Directory",
        "url": "https://cwe.mitre.org/data/definitions/538.html"
    },
    {
        "title": "OWASP: HTTP Methods",
        "url": (
            "https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/"
            "02-Configuration_and_Deployment_Management_Testing/06-Test_HTTP_Methods"
        )
    }
]
