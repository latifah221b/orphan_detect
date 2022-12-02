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
from typing import Optional

from httpx import ReadTimeout, RequestError

from wapitiCore.main.log import log_red, log_verbose, log_orange
from wapitiCore.attack.attack import Attack, PayloadType
from wapitiCore.language.vulnerability import Messages
from wapitiCore.definitions.exec import NAME, WSTG_CODE
from wapitiCore.net.response import Response
from wapitiCore.definitions.resource_consumption import WSTG_CODE as RESOURCE_CONSUMPTION_WSTG_CODE
from wapitiCore.definitions.internal_error import WSTG_CODE as INTERNAL_ERROR_WSTG_CODE
from wapitiCore.net import Request


class ModuleExec(Attack):
    """
    Detect scripts vulnerable to command and/or code execution.
    """

    PAYLOADS_FILE = "execPayloads.txt"

    name = "exec"

    def __init__(self, crawler, persister, attack_options, stop_event, crawler_configuration):
        super().__init__(crawler, persister, attack_options, stop_event, crawler_configuration)
        self.false_positive_timeouts = set()
        self.mutator = self.get_mutator()

    @staticmethod
    def _find_pattern_in_response(data, warned: bool):
        vuln_info = ""
        executed = 0
        if "eval()'d code</b> on line <b>" in data and not warned:
            vuln_info = "Warning eval()"
            warned = True
        if "PATH=" in data and "PWD=" in data:
            vuln_info = "Command execution"
            executed = True
        if "COMPUTERNAME=" in data and "Program" in data:
            vuln_info = "Command execution"
            executed = True
        if "w4p1t1_eval" in data or "1d97830e30da7214d3e121859cfa695f" in data:
            vuln_info = "PHP evaluation"
            executed = True
        if "Cannot execute a blank command in" in data and not warned:
            vuln_info = "Warning exec"
            warned = True
        if "sh: command substitution:" in data and not warned:
            vuln_info = "Warning exec"
            warned = True
        if "Fatal error</b>:  preg_replace" in data and not warned:
            vuln_info = "preg_replace injection"
            warned = True
        if "Warning: usort()" in data and not warned:
            vuln_info = "Warning usort()"
            warned = True
        if "Warning: preg_replace():" in data and not warned:
            vuln_info = "preg_replace injection"
            warned = True
        if "Warning: assert():" in data and not warned:
            vuln_info = "Warning assert"
            warned = True
        if "Failure evaluating code:" in data and not warned:
            vuln_info = "Evaluation warning"
            warned = True
        return vuln_info, executed, warned

    async def attack(self, request: Request, response: Optional[Response] = None):
        warned = False
        timeouted = False
        page = request.path
        saw_internal_error = False
        current_parameter = None
        vulnerable_parameter = False

        for mutated_request, parameter, __, flags in self.mutator.mutate(request):
            if current_parameter != parameter:
                # Forget what we know about current parameter
                current_parameter = parameter
                vulnerable_parameter = False
            elif vulnerable_parameter:
                # If parameter is vulnerable, just skip till next parameter
                continue

            if flags.payload_type == PayloadType.time and request.path_id in self.false_positive_timeouts:
                # If the original request is known to gives timeout and payload is time-based, just skip
                # and move to next payload
                continue

            log_verbose(f"[¨] {mutated_request}")

            try:
                response: Response = await self.crawler.async_send(mutated_request)
            except ReadTimeout:
                if flags.payload_type == PayloadType.time:
                    if await self.does_timeout(request):
                        self.network_errors += 1
                        self.false_positive_timeouts.add(request.path_id)
                        continue

                    vuln_info = "Blind command execution"
                    if parameter == "QUERY_STRING":
                        vuln_message = Messages.MSG_QS_INJECT.format(vuln_info, page)
                    else:
                        vuln_message = f"{vuln_info} via injection in the parameter {parameter}"

                    await self.add_vuln_critical(
                        request_id=request.path_id,
                        category=NAME,
                        request=mutated_request,
                        info=vuln_message,
                        parameter=parameter,
                        wstg=WSTG_CODE
                    )

                    log_red("---")
                    log_red(
                        Messages.MSG_QS_INJECT if parameter == "QUERY_STRING"
                        else Messages.MSG_PARAM_INJECT,
                        vuln_info,
                        page,
                        parameter
                    )
                    log_red(Messages.MSG_EVIL_REQUEST)
                    log_red(mutated_request.http_repr())
                    log_red("---")
                    vulnerable_parameter = True
                    continue

                self.network_errors += 1
                if timeouted:
                    continue

                log_orange("---")
                log_orange(Messages.MSG_TIMEOUT, page)
                log_orange(Messages.MSG_EVIL_REQUEST)
                log_orange(mutated_request.http_repr())
                log_orange("---")

                if parameter == "QUERY_STRING":
                    anom_msg = Messages.MSG_QS_TIMEOUT
                else:
                    anom_msg = Messages.MSG_PARAM_TIMEOUT.format(parameter)

                await self.add_anom_medium(
                    request_id=request.path_id,
                    category=Messages.RES_CONSUMPTION,
                    request=mutated_request,
                    info=anom_msg,
                    parameter=parameter,
                    wstg=RESOURCE_CONSUMPTION_WSTG_CODE
                )
                timeouted = True
            except RequestError:
                self.network_errors += 1
            else:
                # No timeout raised
                vuln_info, executed, warned = self._find_pattern_in_response(response.content, warned)
                if vuln_info:
                    # An error message implies that a vulnerability may exists

                    if parameter == "QUERY_STRING":
                        vuln_message = Messages.MSG_QS_INJECT.format(vuln_info, page)
                        log_message = Messages.MSG_QS_INJECT
                    else:
                        vuln_message = f"{vuln_info} via injection in the parameter {parameter}"
                        log_message = Messages.MSG_PARAM_INJECT

                    await self.add_vuln_critical(
                        request_id=request.path_id,
                        category=NAME,
                        request=mutated_request,
                        info=vuln_message,
                        parameter=parameter,
                        wstg=WSTG_CODE,
                        response=response
                    )

                    log_red("---")
                    log_red(
                        log_message,
                        vuln_info,
                        page,
                        parameter
                    )
                    log_red(Messages.MSG_EVIL_REQUEST)
                    log_red(mutated_request.http_repr())
                    log_red("---")

                    if executed:
                        # We reached maximum exploitation for this parameter, don't send more payloads
                        vulnerable_parameter = True
                        continue

                elif response.is_server_error and not saw_internal_error:
                    saw_internal_error = True
                    if parameter == "QUERY_STRING":
                        anom_msg = Messages.MSG_QS_500
                    else:
                        anom_msg = Messages.MSG_PARAM_500.format(parameter)

                    await self.add_anom_high(
                        request_id=request.path_id,
                        category=Messages.ERROR_500,
                        request=mutated_request,
                        info=anom_msg,
                        parameter=parameter,
                        wstg=INTERNAL_ERROR_WSTG_CODE
                    )

                    log_orange("---")
                    log_orange(Messages.MSG_500, page)
                    log_orange(Messages.MSG_EVIL_REQUEST)
                    log_orange(mutated_request.http_repr())
                    log_orange("---")
