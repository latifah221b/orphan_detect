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

NAME = "XML External Entity"
SHORT_NAME = "XXE"

WSTG_CODE = ["WSTG-INPV-07"]

DESCRIPTION = (
    "An XML External Entity attack is a type of attack against an application that parses XML input."
) + " " + (
    "This attack occurs when XML input containing a reference to an external entity is processed by a weakly "
    "configured XML parser."
) + " " + (
    "This attack may lead to the disclosure of confidential data, denial of service, server side request forgery, "
    "port scanning from the perspective of the machine where the parser is located, and other system impacts."
)

SOLUTION = "The safest way to prevent XXE is always to disable DTDs (External Entities) completely."

REFERENCES = [
    {
        "title": "OWASP: XML External Entity (XXE) Processing",
        "url": "https://owasp.org/www-community/vulnerabilities/XML_External_Entity_(XXE)_Processing"
    },
    {
        "title": "PortSwigger: What is XML external entity injection?",
        "url": "https://portswigger.net/web-security/xxe"
    },
    {
        "title": "CWE-611: Improper Restriction of XML External Entity Reference",
        "url": "https://cwe.mitre.org/data/definitions/611.html"
    },
    {
        "title": "OWASP: XML External Entity Prevention Cheat Sheet",
        "url": "https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html"
    },
    {
        "title": "OWASP: XML Injection",
        "url": (
            "https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/"
            "07-Input_Validation_Testing/07-Testing_for_XML_Injection"
        )
    }
]
