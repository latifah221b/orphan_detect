#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This file is part of the Wapiti project (https://wapiti-scanner.github.io)
# Copyright (C) 2008-2022 Nicolas Surribas
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
import os
from os.path import splitext, join as path_join
from urllib.parse import quote, urlparse
from collections import defaultdict
from enum import Enum
from math import ceil
import random
from types import GeneratorType, FunctionType
from binascii import hexlify
from functools import partialmethod
from typing import Optional
from asyncio import Event

from pkg_resources import resource_filename
from httpx import ReadTimeout, RequestError

from wapitiCore.net.crawler import AsyncCrawler
from wapitiCore.net.classes import CrawlerConfiguration
from wapitiCore.language.vulnerability import CRITICAL_LEVEL, HIGH_LEVEL, MEDIUM_LEVEL, LOW_LEVEL, INFO_LEVEL
from wapitiCore.net.response import Response
from wapitiCore.net.sql_persister import SqlPersister
from wapitiCore.net import Request


all_modules = {
    "backup",
    "brute_login_form",
    "buster",
    "cookieflags",
    "crlf",
    "csp",
    "csrf",
    "drupal_enum",
    "exec",
    "file",
    "htaccess",
    "htp",
    "http_headers",
    "log4shell",
    "methods",
    "nikto",
    "permanentxss",
    "redirect",
    "shellshock",
    "sql",
    "ssl",
    "ssrf",
    "takeover",
    "timesql",
    "wapp",
    "wp_enum",
    "xss",
    "xxe"
}

# Modules that will be used if option -m isn't used
common_modules = {
    "cookieflags",
    "csp",
    "exec",
    "file",
    "http_headers",
    "permanentxss",
    "redirect",
    "sql",
    "ssl",
    "ssrf",
    "xss"
}

# Modules that will be used in passive mode -m passive
passive_modules = {
    "cookieflags",
    "csp",
    "http_headers",
    "wapp"
}

presets = {
    "all": all_modules,
    "common": common_modules,
    "passive": passive_modules
}


VULN = "vulnerability"
ANOM = "anomaly"
ADDITION = "additional"


class PayloadType(Enum):
    pattern = 1
    time = 2
    get = 3
    post = 4
    file = 5
    xss_closing_tag = 6
    xss_non_closing_tag = 7


COMMON_ANNOYING_PARAMETERS = (
    "__VIEWSTATE",
    "__VIEWSTATEENCRYPTED",
    "__VIEWSTATEGENERATOR",
    "__EVENTARGUMENT",
    "__EVENTTARGET",
    "__EVENTVALIDATION",
    "ASPSESSIONID",
    "ASP.NET_SESSIONID",
    "JSESSIONID",
    "CFID",
    "CFTOKEN"
)


def random_string(prefix: str = "w", length: int = 10) -> str:
    """Create a random unique ID that will be used to test injection."""
    # doesn't uppercase letters as BeautifulSoup make some data lowercase
    code = prefix + "".join(
        [random.choice("0123456789abcdefghjijklmnopqrstuvwxyz") for __ in range(0, length - len(prefix))]
    )
    return code


def random_string_with_flags():
    return random_string(), Flags()


class Flags:
    def __init__(
            self,
            payload_type=PayloadType.pattern,
            section="",
            method=PayloadType.get,
            platform="all",
            dbms="all"
    ):
        self.payload_type = payload_type
        self.section = section
        self.method = method
        self.platform = platform
        self.dbms = dbms

    def with_method(self, method):
        return Flags(
            payload_type=self.payload_type,
            section=self.section,
            method=method,
            platform=self.platform,
            dbms=self.dbms
        )

    def with_section(self, section):
        return Flags(
            payload_type=self.payload_type,
            section=section,
            method=self.method,
            platform=self.platform,
            dbms=self.dbms
        )

    def __str__(self):
        return (
            f"Flags(payload_type={self.payload_type}, "
            f"section='{self.section}', "
            f"method={self.method}, "
            f"platform='{self.platform}', "
            f"dbms='{self.dbms}')"
        )

    def __eq__(self, other):
        if not isinstance(other, Flags):
            raise ValueError("Can't compare a Flags object to another kind of object")

        return (
                self.payload_type == other.payload_type and
                self.section == other.section and
                self.method == other.method and
                self.platform == other.platform and
                self.dbms == other.dbms
        )


class Attack:
    """This class represents an attack, it must be extended	for any class which implements a new type of attack"""

    name = "attack"

    do_get = True
    do_post = True

    # List of modules (strings) that must be launched before the current module
    # Must be defined in the code of the module
    require = []

    DATA_DIR = resource_filename("wapitiCore", os.path.join("data", "attacks"))
    HOME_DIR = os.getenv("HOME") or os.getenv("USERPROFILE") or "home"

    PAYLOADS_FILE = None

    # Color codes
    STD = "\033[0;0m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    ORANGE = "\033[0;33m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[1;34m"
    MAGENTA = "\033[0;35m"
    CYAN = "\033[0;36m"
    GB = "\033[0;30m\033[47m"

    allowed = [
        'php', 'html', 'htm', 'xml', 'xhtml', 'xht', 'xhtm',
        'asp', 'aspx', 'php3', 'php4', 'php5', 'txt', 'shtm',
        'shtml', 'phtm', 'phtml', 'jhtml', 'pl', 'jsp', 'cfm',
        'cfml', 'py'
    ]

    # The priority of the module, from 0 (first) to 10 (last). Default is 5
    PRIORITY = 5

    @staticmethod
    def get_resource(resource_path: str):
        return resource_filename("wapitiCore", path_join("data", "attacks", resource_path))

    def __init__(
            self,
            crawler: AsyncCrawler,
            persister: SqlPersister,
            attack_options: dict,
            stop_event: Event,
            crawler_configuration: CrawlerConfiguration):
        super().__init__()
        self._session_id = "".join([random.choice("0123456789abcdefghjijklmnopqrstuvwxyz") for __ in range(0, 6)])
        self.crawler = crawler
        self.persister = persister
        self._stop_event = stop_event
        self.payload_reader = PayloadReader(attack_options)
        self.options = attack_options
        self.crawler_configuration = crawler_configuration

        # List of attack urls already launched in the current module
        self.attacked_get = []
        self.attacked_post = []
        self.network_errors = 0

        self.finished = False

        # List of modules (objects) that must be launched before the current module
        # Must be left empty in the code
        self.deps = []

    async def add_payload(self, payload_type: str, category: str, request_id: int = -1,
                          level=0, request: Request = None, parameter="", info="", wstg: str = None,
                          response: Response = None):
        await self.persister.add_payload(
            request_id=request_id,
            payload_type=payload_type,
            module=self.name,
            category=category,
            level=level,
            request=request,
            parameter=parameter,
            info=info,
            wstg=wstg,
            response=response
        )

    add_vuln = partialmethod(add_payload, payload_type=VULN)
    add_vuln_critical = partialmethod(add_payload, payload_type=VULN, level=CRITICAL_LEVEL)
    add_vuln_high = partialmethod(add_payload, payload_type=VULN, level=HIGH_LEVEL)
    add_vuln_medium = partialmethod(add_payload, payload_type=VULN, level=MEDIUM_LEVEL)
    add_vuln_low = partialmethod(add_payload, payload_type=VULN, level=LOW_LEVEL)
    add_vuln_info = partialmethod(add_payload, payload_type=VULN, level=INFO_LEVEL)

    add_anom_high = partialmethod(add_payload, payload_type=ANOM, level=HIGH_LEVEL)
    add_anom_medium = partialmethod(add_payload, payload_type=ANOM, level=MEDIUM_LEVEL)

    add_addition = partialmethod(add_payload, payload_type=ADDITION, level=INFO_LEVEL)

    @property
    def payloads(self):
        """Load the payloads from the specified file"""
        if self.PAYLOADS_FILE:
            return self.payload_reader.read_payloads(path_join(self.DATA_DIR, self.PAYLOADS_FILE))
        return []

    def load_require(self, dependencies: list = None):
        self.deps = dependencies

    @property
    def attack_level(self):
        return self.options.get("level", 1)

    @property
    def dns_endpoint(self):
        return self.options.get("dns_endpoint", "dns.wapiti3.ovh")

    @property
    def internal_endpoint(self):
        return self.options.get("internal_endpoint", "https://wapiti3.ovh/")

    @property
    def external_endpoint(self):
        return self.options.get("external_endpoint", "http://wapiti3.ovh")

    @property
    def proto_endpoint(self):
        parts = urlparse(self.external_endpoint)
        return parts.netloc + parts.path

    async def must_attack(self, request: Request, response: Optional[Response] = None):  # pylint: disable=unused-argument
        return not self.finished

    @property
    def must_attack_query_string(self):
        return self.attack_level == 2

    async def attack(self, request: Request, response: Optional[Response] = None):
        raise NotImplementedError("Override me bro")

    def get_mutator(self):
        methods = ""
        if self.do_get:
            methods += "G"
        if self.do_post:
            methods += "PF"

        return Mutator(
            methods=methods,
            payloads=self.payloads,
            qs_inject=self.must_attack_query_string,
            skip=self.options.get("skipped_parameters")
        )

    async def does_timeout(self, request):
        try:
            await self.crawler.async_send(request)
        except ReadTimeout:
            return True
        except RequestError:
            pass
        return False


class Mutator:
    def __init__(
            self, methods="FGP", payloads=None, qs_inject=False, max_queries_per_pattern: int = 1000,
            parameters=None,  # Restrict attack to a whitelist of parameters
            skip=None  # Must not attack those parameters (blacklist)
    ):
        self._mutate_get = "G" in methods.upper()
        self._mutate_file = "F" in methods.upper()
        self._mutate_post = "P" in methods.upper()
        self._payloads = payloads
        self._qs_inject = qs_inject
        self._attacks_per_url_pattern = defaultdict(int)
        self._max_queries_per_pattern = max_queries_per_pattern
        self._parameters = parameters if isinstance(parameters, list) else []
        self._skip_list = skip if isinstance(skip, set) else set()
        self._attack_hashes = set()
        self._skip_list.update(COMMON_ANNOYING_PARAMETERS)

    def iter_payloads(self):
        # raise tuples of (payloads, flags)
        if isinstance(self._payloads, tuple):
            yield self._payloads
        elif isinstance(self._payloads, (list, GeneratorType)):
            yield from self._payloads
        elif isinstance(self._payloads, FunctionType):
            result = self._payloads()
            if isinstance(result, GeneratorType):
                yield from result
            else:
                yield result

    def mutate(self, request: Request):
        get_params = request.get_params
        post_params = request.post_params
        file_params = request.file_params
        referer = request.referer

        for params_list in [get_params, post_params, file_params]:
            if params_list is get_params and not self._mutate_get:
                continue

            if params_list is post_params and not self._mutate_post:
                continue

            if params_list is file_params and not self._mutate_file:
                continue

            for i, __ in enumerate(params_list):
                param_name = quote(params_list[i][0])

                if self._skip_list and param_name in self._skip_list:
                    continue

                if self._parameters and param_name not in self._parameters:
                    continue

                saved_value = params_list[i][1]
                if saved_value is None:
                    saved_value = ""

                if params_list is file_params:
                    params_list[i][1] = ["__PAYLOAD__", params_list[i][1][1]]  # second entry is file content
                else:
                    params_list[i][1] = "__PAYLOAD__"

                attack_pattern = Request(
                    request.path,
                    method=request.method,
                    get_params=get_params,
                    post_params=post_params,
                    file_params=file_params
                )

                if hash(attack_pattern) not in self._attack_hashes:
                    self._attack_hashes.add(hash(attack_pattern))

                    for payload, original_flags in self.iter_payloads():

                        if ("[FILE_NAME]" in payload or "[FILE_NOEXT]" in payload) and not request.file_name:
                            continue

                        # no quoting: send() will do it for us
                        payload = payload.replace("[FILE_NAME]", request.file_name)
                        payload = payload.replace("[FILE_NOEXT]", splitext(request.file_name)[0])

                        if isinstance(request.path_id, int):
                            payload = payload.replace("[PATH_ID]", str(request.path_id))

                        payload = payload.replace(
                            "[PARAM_AS_HEX]",
                            hexlify(param_name.encode("utf-8", errors="replace")).decode()
                        )

                        if params_list is file_params:
                            if "[EXTVALUE]" in payload:
                                if "." not in saved_value[0][:-1]:
                                    # Nothing that looks like an extension, skip the payload
                                    continue
                                payload = payload.replace("[EXTVALUE]", saved_value[0].rsplit(".", 1)[-1])

                            # Injection takes place on the filename here
                            payload = payload.replace("[VALUE]", saved_value[0])
                            payload = payload.replace("[DIRVALUE]", saved_value[0].rsplit('/', 1)[0])
                            params_list[i][1] = (payload, saved_value[1], saved_value[2])
                            method = PayloadType.file
                        else:
                            if "[EXTVALUE]" in payload:
                                if "." not in saved_value[:-1]:
                                    # Nothing that looks like an extension, skip the payload
                                    continue
                                payload = payload.replace("[EXTVALUE]", saved_value.rsplit(".", 1)[-1])

                            payload = payload.replace("[VALUE]", saved_value)
                            payload = payload.replace("[DIRVALUE]", saved_value.rsplit('/', 1)[0])
                            params_list[i][1] = payload
                            if params_list is get_params:
                                method = PayloadType.get
                            else:
                                method = PayloadType.post

                        evil_req = Request(
                            request.path,
                            method=request.method,
                            get_params=get_params,
                            post_params=post_params,
                            file_params=file_params,
                            referer=referer,
                            link_depth=request.link_depth
                        )
                        # Flags from iter_payloads should be considered as mutable (even if it's ot the case)
                        # so let's copy them just to be sure we don't mess with them.
                        yield evil_req, param_name, payload, original_flags.with_method(method)

                params_list[i][1] = saved_value

        if not get_params and request.method == "GET" and self._qs_inject:
            attack_pattern = Request(
                f"{request.path}?__PAYLOAD__",
                method=request.method,
                referer=referer,
                link_depth=request.link_depth
            )

            if hash(attack_pattern) not in self._attack_hashes:
                self._attack_hashes.add(hash(attack_pattern))

                for payload, original_flags in self.iter_payloads():
                    # Ignore payloads reusing existing parameter values
                    if "[VALUE]" in payload:
                        continue

                    if "[DIRVALUE]" in payload:
                        continue

                    if ("[FILE_NAME]" in payload or "[FILE_NOEXT]" in payload) and not request.file_name:
                        continue

                    payload = payload.replace("[FILE_NAME]", request.file_name)
                    payload = payload.replace("[FILE_NOEXT]", splitext(request.file_name)[0])

                    if isinstance(request.path_id, int):
                        payload = payload.replace("[PATH_ID]", str(request.path_id))

                    payload = payload.replace(
                        "[PARAM_AS_HEX]",
                        hexlify(b"QUERY_STRING").decode()
                    )

                    evil_req = Request(
                        f"{request.path}?{quote(payload)}",
                        method=request.method,
                        referer=referer,
                        link_depth=request.link_depth
                    )

                    yield evil_req, "QUERY_STRING", payload, original_flags.with_method(PayloadType.get)


class FileMutator:
    def __init__(self, payloads=None, parameters=None, skip=None):
        self._payloads = payloads
        self._attack_hashes = set()
        self._parameters = parameters if isinstance(parameters, list) else []
        self._skip_list = skip if isinstance(skip, set) else set()

    def iter_payloads(self):
        # raise tuples of (payloads, flags)
        if isinstance(self._payloads, tuple):
            yield self._payloads
        elif isinstance(self._payloads, (list, GeneratorType)):
            yield from self._payloads
        elif isinstance(self._payloads, FunctionType):
            result = self._payloads()
            if isinstance(result, GeneratorType):
                yield from result
            else:
                yield result

    def mutate(self, request: Request):
        get_params = request.get_params
        post_params = request.post_params
        referer = request.referer

        for i in range(len(request.file_params)):
            new_params = request.file_params
            param_name = new_params[i][0]

            if self._skip_list and param_name in self._skip_list:
                continue

            if self._parameters and param_name not in self._parameters:
                continue

            for payload, original_flags in self.iter_payloads():

                if ("[FILE_NAME]" in payload or "[FILE_NOEXT]" in payload) and not request.file_name:
                    continue

                # no quoting: send() will do it for us
                payload = payload.replace("[FILE_NAME]", request.file_name)
                payload = payload.replace("[FILE_NOEXT]", splitext(request.file_name)[0])

                if isinstance(request.path_id, int):
                    payload = payload.replace("[PATH_ID]", str(request.path_id))

                payload = payload.replace(
                    "[PARAM_AS_HEX]",
                    hexlify(param_name.encode("utf-8", errors="replace")).decode()
                )

                # httpx needs bytes as content value
                new_params[i][1] = ("content.xml", payload.encode(errors="replace"), "text/xml")

                evil_req = Request(
                    request.path,
                    method=request.method,
                    get_params=get_params,
                    post_params=post_params,
                    file_params=new_params,
                    referer=referer,
                    link_depth=request.link_depth
                )
                # Flags from iter_payloads should be considered as mutable (even if it's ot the case)
                # so let's copy them just to be sure we don't mess with them.
                yield evil_req, param_name, payload, original_flags.with_method(PayloadType.file)


class PayloadReader:
    """Class for reading and writing in text files"""

    def __init__(self, options):
        self._timeout = options["timeout"]
        self._endpoint_url = options.get("external_endpoint", "http://wapiti3.ovh/")

    def read_payloads(self, filename):
        """returns a array"""
        lines = []
        try:
            with open(filename, errors="ignore", encoding='utf-8') as file:
                for line in file:
                    clean_line, flags = self.process_line(line)
                    if clean_line:
                        lines.append((clean_line, flags))
        except IOError as exception:
            print(exception)
        return lines

    def process_line(self, line):
        flag_type = PayloadType.pattern
        clean_line = line.strip(" \n")
        clean_line = clean_line.replace("[TAB]", "\t")
        clean_line = clean_line.replace("[LF]", "\n")
        clean_line = clean_line.replace("[FF]", "\f")  # Form feed
        clean_line = clean_line.replace("[TIME]", str(int(ceil(self._timeout)) + 1))
        clean_line = clean_line.replace("[EXTERNAL_ENDPOINT]", self._endpoint_url)

        if "[TIMEOUT]" in clean_line:
            flag_type = PayloadType.time
            clean_line = clean_line.replace("[TIMEOUT]", "")

        clean_line = clean_line.replace("\\0", "\0")

        return clean_line, Flags(payload_type=flag_type)
