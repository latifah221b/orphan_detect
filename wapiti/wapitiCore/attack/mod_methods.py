#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This file is part of the Wapiti project (https://wapiti-scanner.github.io)
# Copyright (C) 2018-2022 Nicolas Surribas
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
from typing import Optional

from httpx import RequestError

from wapitiCore.main.log import log_verbose, log_orange

from wapitiCore.attack.attack import Attack
from wapitiCore.definitions.methods import NAME, WSTG_CODE
from wapitiCore.net import Request, Response


class ModuleMethods(Attack):
    """
    Detect uncommon HTTP methods (like PUT) that may be allowed by a script.
    """

    name = "methods"
    PRIORITY = 6
    KNOWN_METHODS = {"GET", "POST", "OPTIONS", "HEAD", "TRACE"}
    do_get = True
    do_post = True
    excluded_path = set()

    async def must_attack(self, request: Request, response: Optional[Response] = None):
        return request.path not in self.excluded_path

    async def attack(self, request: Request, response: Optional[Response] = None):
        page = request.path
        self.excluded_path.add(page)

        option_request = Request(
            page,
            "OPTIONS",
            referer=request.referer,
            link_depth=request.link_depth
        )

        log_verbose(f"[+] {option_request}")

        try:
            response = await self.crawler.async_send(option_request)
        except RequestError:
            self.network_errors += 1
            return

        if response.is_success or response.is_redirect:
            methods = response.headers.get("allow", '').upper().split(',')
            methods = {method.strip() for method in methods if method.strip()}
            interesting_methods = sorted(methods - self.KNOWN_METHODS)

            if interesting_methods:
                log_orange("---")
                log_orange(f"Interesting methods allowed on {page}: {', '.join(interesting_methods)}")
                await self.add_addition(
                    category=NAME,
                    request=option_request,
                    info=f"Interesting methods allowed on {page}: {', '.join(interesting_methods)}",
                    wstg=WSTG_CODE,
                    response=response
                )
                log_orange("---")
