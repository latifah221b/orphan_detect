TYPE = "vulnerability"

NAME = "Fingerprint web server"
SHORT_NAME = NAME

WSTG_CODE = ["WSTG-INFO-02"]

DESCRIPTION = "The version of a web server can be identified due to the presence of its specific fingerprints."

SOLUTION = "This is only for informational purposes."

REFERENCES = [
    {
        "title": "OWASP: Fingerprint Web Server",
        "url": (
            "https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/"
            "01-Information_Gathering/02-Fingerprint_Web_Server.html"
        )
    }
]
