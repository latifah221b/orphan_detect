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
TYPE = "additional"

NAME = "Fingerprint web technology"
SHORT_NAME = NAME

WSTG_CODE = ["WSTG-INFO-02", "WSTG-INFO-08"]

DESCRIPTION = "The use of a web technology can be deducted due to the presence of its specific fingerprints."

SOLUTION = "This is only for informational purposes."

REFERENCES = [
    {
        "title": "OWASP: Fingerprint Web Server",
        "url": (
            "https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/"
            "01-Information_Gathering/02-Fingerprint_Web_Server.html"
        )
    },
    {
        "title": "OWASP: Fingerprint Web Application Framework",
        "url": (
            "https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/"
            "01-Information_Gathering/08-Fingerprint_Web_Application_Framework.html"
        )
    }
]
