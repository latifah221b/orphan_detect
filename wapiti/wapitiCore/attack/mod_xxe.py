#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This file is part of the Wapiti project (https://wapiti-scanner.github.io)
# Copyright (C) 2019-2022 Nicolas Surribas
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
from binascii import unhexlify
from asyncio import sleep
from typing import Optional
from urllib.parse import quote
from configparser import ConfigParser
from os.path import join as path_join

from httpx import ReadTimeout, RequestError

from wapitiCore.main.log import logging, log_red, log_orange, log_verbose
from wapitiCore.attack.attack import Attack, FileMutator, Mutator, PayloadReader, Flags
from wapitiCore.language.vulnerability import Messages
from wapitiCore.definitions.xxe import NAME, WSTG_CODE
from wapitiCore.definitions.resource_consumption import WSTG_CODE as RESOURCE_CONSUMPTION_WSTG_CODE
from wapitiCore.definitions.internal_error import WSTG_CODE as INTERNAL_ERROR_WSTG_CODE
from wapitiCore.net import Request, Response


def search_pattern(content: str, patterns: list) -> str:
    for pattern in patterns:
        if pattern in content:
            return pattern
    return ""


class ModuleXxe(Attack):
    """Detect scripts vulnerable to XML external entity injection (also known as XXE)."""

    name = "xxe"
    do_get = True
    do_post = True

    PAYLOADS_FILE = "xxePayloads.ini"
    MSG_VULN = "XXE vulnerability"

    def __init__(self, crawler, persister, attack_options, stop_event, crawler_configuration):
        Attack.__init__(self, crawler, persister, attack_options, stop_event, crawler_configuration)
        self.vulnerables = set()
        self.attacked_urls = set()
        self.payload_to_rules = {}
        self.mutator = self.get_mutator()

    @property
    def payloads(self):
        """Load the payloads from the specified file"""
        if not self.PAYLOADS_FILE:
            return []

        payloads = []

        config_reader = ConfigParser(interpolation=None)
        with open(path_join(self.DATA_DIR, self.PAYLOADS_FILE), encoding='utf-8') as payload_file:
            config_reader.read_file(payload_file)

        # No time based payloads here so we don't care yet
        reader = PayloadReader(self.options)

        for section in config_reader.sections():
            clean_payload, flags = reader.process_line(config_reader[section]["payload"])
            clean_payload = clean_payload.replace("[SESSION_ID]", self._session_id)

            rules = config_reader[section]["rules"].splitlines()
            self.payload_to_rules[section] = rules

            payloads.append((clean_payload, flags.with_section(section)))

        return payloads

    def get_mutator(self):
        methods = ""
        if self.do_get:
            methods += "G"
        if self.do_post:
            # No file uploads, we won't attack filenames but file contents
            methods += "P"

        return Mutator(
            methods=methods,
            payloads=self.payloads,
            qs_inject=self.must_attack_query_string,
            skip=self.options.get("skipped_parameters")
        )

    async def false_positive(self, request: Request, pattern: str) -> bool:
        try:
            response = await self.crawler.async_send(request)
        except RequestError:
            self.network_errors += 1
            return False
        else:
            return pattern in response.content

    def flag_to_patterns(self, flags):
        try:
            return self.payload_to_rules[flags.section]
        except AttributeError:
            return []

    async def attack(self, request: Request, response: Optional[Response] = None):
        timeouted = False
        page = request.path
        saw_internal_error = False
        current_parameter = None
        vulnerable_parameter = False

        if request.url not in self.attacked_urls:
            await self.attack_body(request)
            self.attacked_urls.add(request.url)

        if request.path_id in self.vulnerables:
            return

        if request.is_multipart:
            await self.attack_upload(request)
            if request.path_id in self.vulnerables:
                return

        for mutated_request, parameter, __, flags in self.mutator.mutate(request):
            if current_parameter != parameter:
                # Forget what we know about current parameter
                current_parameter = parameter
                vulnerable_parameter = False
            elif vulnerable_parameter:
                # If parameter is vulnerable, just skip till next parameter
                continue

            log_verbose(f"[¨] {mutated_request}")

            try:
                response = await self.crawler.async_send(mutated_request)
            except ReadTimeout:
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
                continue
            else:
                pattern = search_pattern(response.content, self.flag_to_patterns(flags))
                if pattern and not await self.false_positive(request, pattern):
                    # An error message implies that a vulnerability may exist
                    if parameter == "QUERY_STRING":
                        vuln_message = Messages.MSG_QS_INJECT.format(self.MSG_VULN, page)
                    else:
                        vuln_message = f"{self.MSG_VULN} via injection in the parameter {parameter}"

                    await self.add_vuln_high(
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
                        Messages.MSG_QS_INJECT if parameter == "QUERY_STRING" else Messages.MSG_PARAM_INJECT,
                        self.MSG_VULN,
                        page,
                        parameter
                    )
                    log_red(Messages.MSG_EVIL_REQUEST)
                    log_red(mutated_request.http_repr())
                    log_red("---")

                    # We reached maximum exploitation for this parameter, don't send more payloads
                    vulnerable_parameter = True
                    continue

                if response.is_server_error and not saw_internal_error:
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
                        wstg=INTERNAL_ERROR_WSTG_CODE,
                        response=response
                    )

                    log_orange("---")
                    log_orange(Messages.MSG_500, page)
                    log_orange(Messages.MSG_EVIL_REQUEST)
                    log_orange(mutated_request.http_repr())
                    log_orange("---")

    async def attack_body(self, original_request):
        for payload, tags in self.payloads:
            payload = payload.replace("[PATH_ID]", str(original_request.path_id))
            payload = payload.replace("[PARAM_AS_HEX]", "72617720626f6479")  # raw body
            mutated_request = Request(original_request.url, method="POST", enctype="text/xml", post_params=payload)

            log_verbose(f"[¨] {mutated_request}")

            try:
                response = await self.crawler.async_send(mutated_request)
            except RequestError:
                self.network_errors += 1
                continue
            else:
                pattern = search_pattern(response.content, self.flag_to_patterns(tags))
                if pattern and not await self.false_positive(original_request, pattern):
                    await self.add_vuln_high(
                        request_id=original_request.path_id,
                        category=NAME,
                        request=mutated_request,
                        info="XXE vulnerability leading to file disclosure",
                        parameter="raw body",
                        wstg=WSTG_CODE,
                        response=response
                    )

                    log_red("---")
                    log_red(
                        "{0} in {1} leading to file disclosure",
                        self.MSG_VULN,
                        original_request.url
                    )
                    log_red(Messages.MSG_EVIL_REQUEST)
                    log_red(mutated_request.http_repr())
                    log_red("---")
                    self.vulnerables.add(original_request.path_id)
                    break

    async def attack_upload(self, original_request):
        mutator = FileMutator(payloads=self.payloads)
        current_parameter = None
        vulnerable_parameter = False

        for mutated_request, parameter, _payload, flags in mutator.mutate(original_request):
            if current_parameter != parameter:
                # Forget what we know about current parameter
                current_parameter = parameter
                vulnerable_parameter = False
            elif vulnerable_parameter:
                # If parameter is vulnerable, just skip till next parameter
                continue

            log_verbose(f"[¨] {mutated_request}")

            try:
                response = await self.crawler.async_send(mutated_request)
            except RequestError:
                self.network_errors += 1
            else:
                pattern = search_pattern(response.content, self.flag_to_patterns(flags))
                if pattern and not await self.false_positive(original_request, pattern):
                    await self.add_vuln_high(
                        request_id=original_request.path_id,
                        category=NAME,
                        request=mutated_request,
                        info="XXE vulnerability leading to file disclosure",
                        parameter=parameter,
                        wstg=WSTG_CODE,
                        response=response
                    )

                    log_red("---")
                    log_red(
                        Messages.MSG_PARAM_INJECT,
                        self.MSG_VULN,
                        original_request.url,
                        parameter
                    )
                    log_red(Messages.MSG_EVIL_REQUEST)
                    log_red(mutated_request.http_repr())
                    log_red("---")
                    vulnerable_parameter = True
                    self.vulnerables.add(original_request.path_id)

    async def finish(self):
        endpoint_url = f"{self.internal_endpoint}get_xxe.php?session_id={self._session_id}"
        logging.info(f"[*] Asking endpoint URL {endpoint_url} for results, please wait...")
        await sleep(2)
        # A la fin des attaques on questionne le endpoint pour savoir s'il a été contacté
        endpoint_request = Request(endpoint_url)
        try:
            response = await self.crawler.async_send(endpoint_request)
        except RequestError:
            self.network_errors += 1
            logging.error(f"[!] Unable to request endpoint URL '{self.internal_endpoint}'")
            return

        data = response.json
        if not isinstance(data, dict):
            return

        for request_id in data:
            original_request = await self.persister.get_path_by_id(request_id)
            if original_request is None:
                continue
                # raise ValueError("Could not find the original request with ID {}".format(request_id))

            page = original_request.path
            for hex_param in data[request_id]:
                parameter = unhexlify(hex_param).decode("utf-8")

                for infos in data[request_id][hex_param]:
                    request_url = infos["url"]
                    # Date in ISO format
                    request_date = infos["date"]
                    request_ip = infos["ip"]
                    request_size = infos["size"]
                    payload_name = infos["payload"]

                    if parameter == "QUERY_STRING":
                        vuln_message = Messages.MSG_QS_INJECT.format(self.MSG_VULN, page)
                    elif parameter == "raw body":
                        vuln_message = f"Out-Of-Band {self.MSG_VULN} by sending raw XML in request body"
                    else:
                        vuln_message = f"Out-Of-Band {self.MSG_VULN} via injection in the parameter {parameter}"

                    if not request_size:
                        # Overwrite the message as the full exploit chain failed
                        vuln_message = (
                            "The target reached the DTD file on the endpoint but the exploitation didn't succeed."
                        )
                    else:
                        # Exploitation succeed, we have some data
                        more_infos = (
                            f"The target sent {request_size} bytes of data to the endpoint at {request_date} "
                            f"with IP {request_ip}.\n"
                            f"Received data can be seen at {request_url}."
                        )
                        vuln_message += "\n" + more_infos

                    # placeholder if shit happens
                    payload = (
                        "<xml>"
                        "See https://phonexicum.github.io/infosec/xxe.html#attack-vectors"
                        "</xml>"
                    )

                    for payload, _flags in self.payloads:
                        if f"{payload_name}.dtd" in payload:
                            payload = payload.replace("[PATH_ID]", str(original_request.path_id))
                            payload = payload.replace("[PARAM_AS_HEX]", "72617720626f6479")
                            break

                    if parameter == "raw body":
                        mutated_request = Request(
                            original_request.path,
                            method="POST",
                            enctype="text/xml",
                            post_params=payload
                        )
                    elif parameter == "QUERY_STRING":
                        mutated_request = Request(
                            f"{original_request.path}?{quote(payload)}",
                            method="GET"
                        )
                    elif parameter in original_request.get_keys or parameter in original_request.post_keys:
                        mutator = Mutator(
                            methods="G" if original_request.method == "GET" else "P",
                            payloads=[(payload, Flags())],
                            qs_inject=self.must_attack_query_string,
                            parameters=[parameter],
                            skip=self.options.get("skipped_parameters")
                        )

                        mutated_request, __, __, __ = next(mutator.mutate(original_request))
                    else:
                        mutator = FileMutator(
                            payloads=[(payload, Flags())],
                            parameters=[parameter],
                            skip=self.options.get("skipped_parameters")
                        )
                        mutated_request, __, __, __ = next(mutator.mutate(original_request))

                    if request_size:
                        add_vuln_method = self.add_vuln_high
                        log_method = log_red
                    else:
                        add_vuln_method = self.add_vuln_medium
                        log_method = log_orange

                    await add_vuln_method(
                        request_id=original_request.path_id,
                        category=NAME,
                        request=mutated_request,
                        info=vuln_message,
                        parameter=parameter,
                        wstg=WSTG_CODE
                    )

                    log_method("---")
                    log_method(vuln_message)
                    log_method(Messages.MSG_EVIL_REQUEST)
                    log_method(mutated_request.http_repr())
                    log_method("---")
