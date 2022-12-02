#!/usr/bin/env python3
import sys
from multiprocessing import cpu_count

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

VERSION = "3.1.4"
DOC_DIR = "share/doc/wapiti"


class PyTest(TestCommand):
    user_options = [("pytest-args=", "a", "Arguments to pass into py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        try:
            self.pytest_args = ["-n", str(cpu_count()), "--boxed"]
        except (ImportError, NotImplementedError):
            self.pytest_args = ["-n", "1", "--boxed"]

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest

        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


doc_and_conf_files = [
    (
        DOC_DIR,
        [
            "doc/AUTHORS",
            "doc/ChangeLog_Wapiti",
            "doc/ChangeLog_lswww",
            "doc/endpoints.md",
            "doc/example.txt",
            "doc/FAQ.md",
            "doc/wapiti.1.html",
            "doc/wapiti.ronn",
            "doc/wapiti-getcookie.1.html",
            "doc/wapiti-getcookie.ronn",
            "doc/xxe_module.md",
            "LICENSE",
            "INSTALL.md",
            "README.rst",
            "VERSION"
        ]
    ),
    (
        "share/man/man1",
        [
            "doc/wapiti.1",
            "doc/wapiti-getcookie.1"
        ]
    )
]

# Main
setup(
    name="wapiti3",
    version=VERSION,
    description="A web application vulnerability scanner",
    long_description="""\
Wapiti allows you to audit the security of your web applications.
It performs "black-box" scans, i.e. it does not study the source code of the
application but will scans the webpages of the deployed webapp, looking for
scripts and forms where it can inject data.
Once it gets this list, Wapiti acts like a fuzzer, injecting payloads to see
if a script is vulnerable.""",
    url="https://wapiti-scanner.github.io/",
    author="Nicolas Surribas",
    author_email="nicolas.surribas@gmail.com",
    license="GPLv2",
    platforms=["Any"],
    packages=find_packages(exclude=["tests", "tests.*"]),
    data_files=doc_and_conf_files,
    include_package_data=True,
    scripts=[
        "bin/wapiti",
        "bin/wapiti-getcookie"
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Natural Language :: English",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: Unix",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Security",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Software Development :: Testing"
    ],
    install_requires=[
        "beautifulsoup4>=4.10.0",
        "tld>=0.12.5",
        "yaswfp>=0.9.3",
        "mako>=1.1.4",
        "markupsafe==2.1.1",
        "six>=1.15.0",
        "browser-cookie3==0.16.2",
        "cryptography==36.0.2",
        "httpx[brotli, socks]==0.23.0",
        "sqlalchemy>=1.4.26",
        "aiocache==0.11.1",
        "aiosqlite==0.17.0",
        "aiohttp==3.8.1",
        "loguru>=0.5.3",
        "dnspython==2.1.0",
        "httpcore==0.15.0",
        "mitmproxy==8.0.0",
        "h11==0.12",
        "pyasn1==0.4.8",
        "arsenic==21.8",
        "pyasn1==0.4.8",
    ],
    extras_require={
        "NTLM": ["httpx-ntlm"],
        "sslyze": [
            "sslyze==5.0.6",
            "humanize==4.4.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "wapiti = wapitiCore.main.wapiti:wapiti_asyncio_wrapper",
            "wapiti-getcookie = wapitiCore.main.getcookie:getcookie_asyncio_wrapper",
        ],
    },
    # https://buildmedia.readthedocs.org/media/pdf/pytest/3.6.0/pytest.pdf
    tests_require=["pytest>=6.2.2", "respx==0.20.0", "pytest-cov>=2.11.1", "pytest-asyncio==0.20.1"],
    setup_requires=["pytest-runner"],
    cmdclass={"test": PyTest}
)
