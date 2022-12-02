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

NAME = "Potentially dangerous file"
SHORT_NAME = NAME

WSTG_CODE = ["WSTG-CONF-04", "WSTG-CONF-01"]

DESCRIPTION = "A file with potential vulnerabilities has been found on the website."

SOLUTION = "Make sure the script is up-to-date and restrict access to it if possible."

REFERENCES = [
    {
        "title": "Mitre: Search details of a CVE",
        "url": "https://cve.mitre.org/cve/search_cve_list.html"
    },
    {
        "title": "OWASP: Test Network Infrastructure Configuration",
        "url": (
            "https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/"
            "02-Configuration_and_Deployment_Management_Testing/01-Test_Network_Infrastructure_Configuration"
        )
    }
]
