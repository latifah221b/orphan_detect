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
from urllib.parse import quote
from os.path import join as path_join
from typing import Optional

from httpx import ReadTimeout, RequestError

from wapitiCore.main.log import log_red, log_orange, log_verbose
from wapitiCore.attack.attack import Attack, PayloadType, Mutator, random_string
from wapitiCore.language.vulnerability import Messages
from wapitiCore.definitions.stored_xss import NAME, WSTG_CODE
from wapitiCore.definitions.internal_error import WSTG_CODE as INTERNAL_ERROR_WSTG_CODE
from wapitiCore.definitions.resource_consumption import WSTG_CODE as RESOURCE_CONSUMPTION_WSTG_CODE
from wapitiCore.net import Request, Response
from wapitiCore.net.xss_utils import generate_payloads, valid_xss_content_type, check_payload
from wapitiCore.net.csp_utils import has_strong_csp
from wapitiCore.parsers.html_parser import Html


class ModulePermanentxss(Attack):
    """
    Detect stored (aka permanent) Cross-Site Scripting vulnerabilities on the web server.
    """

    name = "permanentxss"
    require = ["xss"]
    PRIORITY = 6

    # Attempted payload injection from mod_xss.
    # key is tainted value, dict values are (mutated_request, parameter, flags)
    tried_xss = {}

    # key = xss code, valid = (payload, flags)
    successful_xss = {}

    PAYLOADS_FILE = path_join(Attack.DATA_DIR, "xssPayloads.ini")

    MSG_VULN = "Stored XSS vulnerability"

    RANDOM_WEBSITE = f"https://{random_string(length=6)}.com/"

    @property
    def external_endpoint(self):
        return self.RANDOM_WEBSITE

    async def must_attack(self, request: Request, response: Optional[Response] = None):
        if not valid_xss_content_type(response) or response.status in (301, 302, 303):
            # If that content-type can't be interpreted as HTML by browsers then it is useless
            # Same goes for redirections
            return False

        return True

    async def attack(self, request: Request, response: Optional[Response] = None):
        """This method searches XSS which could be permanently stored in the web application"""
        headers = {}

        if request.referer:
            headers["referer"] = request.referer

        try:
            response = await self.crawler.async_send(Request(request.url), headers=headers)
            data = response.content
        except RequestError:
            self.network_errors += 1
            return

        html = Html(response.content, request.url)

        # Should we look for taint codes sent with GET in the webpages?
        # Exploiting those may imply sending more GET requests

        # Search in the page source for every taint code used by mod_xss
        for taint in self.tried_xss:
            input_request = self.tried_xss[taint][0]

            # Such situations should not occur as it would be stupid to block POST (or GET) requests for mod_xss
            # and not mod_permanentxss, but it is possible so let's filter that.
            if not self.do_get and input_request.method == "GET":
                continue

            if not self.do_post and input_request.method == "POST":
                continue

            if taint.lower() in data.lower():
                # Code found in the webpage !
                # Did mod_xss saw this as a reflected XSS ?
                if taint in self.successful_xss:
                    # Yes, it means XSS payloads were injected, not just tainted code.
                    payload, flags = self.successful_xss[taint]

                    if check_payload(
                        self.DATA_DIR,
                        self.PAYLOADS_FILE,
                        self.external_endpoint,
                        self.proto_endpoint,
                        html,
                        flags,
                        taint
                    ):
                        # If we can find the payload again, this is in fact a stored XSS
                        get_params = input_request.get_params
                        post_params = input_request.post_params
                        file_params = input_request.file_params
                        referer = input_request.referer

                        # The following trick may seems dirty but it allows to treat GET and POST requests
                        # the same way.
                        for params_list in [get_params, post_params, file_params]:
                            for i, __ in enumerate(params_list):
                                parameter, value = params_list[i]
                                parameter = quote(parameter)
                                if value != taint:
                                    continue

                                if params_list is file_params:
                                    params_list[i][1][0] = payload
                                else:
                                    params_list[i][1] = payload

                                # we found the xss payload again -> stored xss vuln
                                evil_request = Request(
                                    input_request.path,
                                    method=input_request.method,
                                    get_params=get_params,
                                    post_params=post_params,
                                    file_params=file_params,
                                    referer=referer
                                )

                                if request.path == input_request.path:
                                    description = (
                                        f"Permanent XSS vulnerability found via injection in the parameter {parameter}"
                                    )
                                else:
                                    description = (
                                        f"Permanent XSS vulnerability found in {request.url} by injecting"
                                        f" the parameter {parameter} of {input_request.path}"
                                    )
                                if has_strong_csp(response, html):
                                    description += ".\nWarning: Content-Security-Policy is present!"

                                await self.add_vuln_high(
                                    request_id=request.path_id,
                                    category=NAME,
                                    request=evil_request,
                                    parameter=parameter,
                                    info=description,
                                    wstg=WSTG_CODE
                                )

                                if parameter == "QUERY_STRING":
                                    injection_msg = Messages.MSG_QS_INJECT
                                else:
                                    injection_msg = Messages.MSG_PARAM_INJECT

                                log_red("---")
                                log_red(
                                    injection_msg,
                                    self.MSG_VULN,
                                    request.path,
                                    parameter
                                )

                                if has_strong_csp(response, html):
                                    log_red("Warning: Content-Security-Policy is present!")

                                log_red(Messages.MSG_EVIL_REQUEST)
                                log_red(evil_request.http_repr())
                                log_red("---")
                                # FIX: search for the next code in the webpage

                # Ok the content is stored, but will we be able to inject javascript?
                else:
                    parameter = self.tried_xss[taint][1]
                    payloads = generate_payloads(response.content, taint, self.PAYLOADS_FILE, self.external_endpoint)
                    flags = self.tried_xss[taint][2]

                    # TODO: check that and make it better
                    if flags.method == PayloadType.get:
                        method = "G"
                    elif flags.method == PayloadType.file:
                        method = "F"
                    else:
                        method = "P"

                    await self.attempt_exploit(method, payloads, input_request, parameter, taint, request)

    def load_require(self, dependencies: list = None):
        if dependencies:
            for module in dependencies:
                if module.name == "xss":
                    self.successful_xss = module.successful_xss
                    self.tried_xss = module.tried_xss

    async def attempt_exploit(self, method, payloads, injection_request, parameter, taint, output_request):
        timeouted = False
        page = injection_request.path
        saw_internal_error = False
        output_url = output_request.url

        attack_mutator = Mutator(
            methods=method,
            payloads=payloads,
            qs_inject=self.must_attack_query_string,
            parameters=[parameter],
            skip=self.options.get("skipped_parameters")
        )

        for evil_request, xss_param, _xss_payload, xss_flags in attack_mutator.mutate(injection_request):
            log_verbose(f"[¨] {evil_request}")

            try:
                evil_response = await self.crawler.async_send(evil_request)
            except ReadTimeout:
                self.network_errors += 1
                if timeouted:
                    continue

                log_orange("---")
                log_orange(Messages.MSG_TIMEOUT, page)
                log_orange(Messages.MSG_EVIL_REQUEST)
                log_orange(evil_request.http_repr())
                log_orange("---")

                if xss_param == "QUERY_STRING":
                    anom_msg = Messages.MSG_QS_TIMEOUT
                else:
                    anom_msg = Messages.MSG_PARAM_TIMEOUT.format(xss_param)

                await self.add_anom_medium(
                    request_id=injection_request.path_id,
                    category=Messages.RES_CONSUMPTION,
                    request=evil_request,
                    info=anom_msg,
                    parameter=xss_param,
                    wstg=RESOURCE_CONSUMPTION_WSTG_CODE
                )
                timeouted = True
            except RequestError:
                self.network_errors += 1
                continue
            else:
                try:
                    response = await self.crawler.async_send(output_request)
                except RequestError:
                    self.network_errors += 1
                    continue

                html = Html(response.content, output_url)

                if (
                        not response.is_redirect and
                        valid_xss_content_type(evil_response) and  # TODO: check this twice
                        check_payload(
                            self.DATA_DIR,
                            self.PAYLOADS_FILE,
                            self.external_endpoint,
                            self.proto_endpoint,
                            html,
                            xss_flags,
                            taint
                        )
                ):

                    if page == output_request.path:
                        description = (
                            f"Permanent XSS vulnerability found via injection in the parameter {xss_param}"
                        )
                    else:
                        description = (
                            f"Permanent XSS vulnerability found in {output_request.url} by injecting"
                            f" the parameter {parameter} of {page}"
                        )

                    if has_strong_csp(response, html):
                        description += ".\nWarning: Content-Security-Policy is present!"

                    await self.add_vuln_high(
                        request_id=injection_request.path_id,
                        category=NAME,
                        request=evil_request,
                        parameter=xss_param,
                        info=description,
                        wstg=WSTG_CODE,
                        response=response
                    )

                    if xss_param == "QUERY_STRING":
                        injection_msg = Messages.MSG_QS_INJECT
                    else:
                        injection_msg = Messages.MSG_PARAM_INJECT

                    log_red("---")
                    # TODO: a last parameter should give URL used to pass the vulnerable parameter
                    log_red(
                        injection_msg,
                        self.MSG_VULN,
                        output_url,
                        xss_param
                    )

                    if has_strong_csp(response, html):
                        log_red("Warning: Content-Security-Policy is present!")

                    log_red(Messages.MSG_EVIL_REQUEST)
                    log_red(evil_request.http_repr())
                    log_red("---")

                    # stop trying payloads and jump to the next parameter
                    break
                if response.is_server_error and not saw_internal_error:
                    if xss_param == "QUERY_STRING":
                        anom_msg = Messages.MSG_QS_500
                    else:
                        anom_msg = Messages.MSG_PARAM_500.format(xss_param)

                    await self.add_anom_high(
                        request_id=injection_request.path_id,
                        category=Messages.ERROR_500,
                        request=evil_request,
                        info=anom_msg,
                        parameter=xss_param,
                        wstg=INTERNAL_ERROR_WSTG_CODE,
                        response=response
                    )

                    log_orange("---")
                    log_orange(Messages.MSG_500, page)
                    log_orange(Messages.MSG_EVIL_REQUEST)
                    log_orange(evil_request.http_repr())
                    log_orange("---")
                    saw_internal_error = True
