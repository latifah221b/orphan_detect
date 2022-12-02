#!/usr/bin/env python3
# -*- coding: utf-8 -*-
TYPE = "additional"

NAME = "HTTP Methods"
SHORT_NAME = NAME

WSTG_CODE = ["WSTG-CONF-06"]

DESCRIPTION = (
    "While GET and POST are by far the most common methods that are used to access "
    "information provided by a web server, HTTP allows several other (and somewhat less known) methods."
) + " " + (
    "Some of these can be used for nefarious purposes if the web server is misconfigured."
)

SOLUTION = (
    "This is only for informational purposes."
)

REFERENCES = [
    {
        "title": "OWASP: HTTP Methods",
        "url": (
            "https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/"
            "02-Configuration_and_Deployment_Management_Testing/06-Test_HTTP_Methods"
        )
    }
]
