#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This file is part of the Wapiti project (https://wapiti-scanner.github.io)
# Copyright (C) 2006-2022 Nicolas SURRIBAS
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
import asyncio
import codecs
import os
import signal
import sys
from importlib import import_module
from inspect import getdoc
from sqlite3 import OperationalError
from urllib.parse import urlparse

import httpx
from httpx import RequestError
from wapitiCore.attack.attack import (all_modules, common_modules)
from wapitiCore.controller.wapiti import InvalidOptionValue, module_to_class_name, Wapiti
from wapitiCore.main.banners import print_banner
from wapitiCore.parsers.commandline import parse_args
from wapitiCore.main.log import logging
from wapitiCore.net.classes import HttpCredential, FormCredential, RawCredential
from wapitiCore.net.auth import async_try_form_login, load_form_script, check_http_auth, login_with_raw_data
from wapitiCore.net import Request
from wapitiCore.report import GENERATORS

global_stop_event = asyncio.Event()


def inner_ctrl_c_signal_handler():  # pylint: disable=unused-argument
    logging.info("Waiting for running crawler tasks to finish, please wait.")
    global_stop_event.set()


def stop_attack_process():  # pylint: disable=unused-argument
    logging.info("Waiting for all payload tasks to finish for current resource, please wait.")
    global_stop_event.set()


def fix_url_path(url: str):
    """Fix the url path if it's not defined"""
    return url if urlparse(url).path else url + '/'


def is_valid_endpoint(url_type, url: str):
    """Verify if the url provided has the right format"""
    try:
        parts = urlparse(url)
    except ValueError:
        logging.error('ValueError')
        return False
    else:
        if parts.params or parts.query or parts.fragment:
            logging.error(f"Error: {url_type} must not contain params, query or fragment!")
            return False
        if parts.scheme in ("http", "https") and parts.netloc:
            return True
    logging.error(f"Error: {url_type} must contain scheme and host")
    return False


def ping(url: str):
    try:
        httpx.get(url, timeout=5)
    except RequestError:
        return False
    return True


async def wapiti_main():
    print_banner()
    args = parse_args()

    if args.tasks < 1:
        logging.error("Number of concurrent tasks must be 1 or above!")
        sys.exit(2)

    if args.scope == "punk":
        print("[*] Do you feel lucky punk?")

    if args.list_modules:
        print("[*] Available modules:")
        for module_name in sorted(all_modules):
            try:
                mod = import_module("wapitiCore.attack.mod_" + module_name)
                class_name = module_to_class_name(module_name)
                is_common = " (used by default)" if module_name in common_modules else ""
                print(f"\t{module_name}{is_common}")
                print("\t\t" + getdoc(getattr(mod, class_name)))
                print('')
            except ImportError:
                continue
        sys.exit()

    url = fix_url_path(args.base_url)
    if args.data:
        base_request = Request(
            url,
            method="POST",
            post_params=args.data
        )
    else:
        base_request = Request(url)

    parts = urlparse(url)
    if not parts.scheme or not parts.netloc:
        logging.error("Invalid base URL was specified, please give a complete URL with protocol scheme.")
        sys.exit()

    wap = Wapiti(base_request, scope=args.scope, session_dir=args.store_session, config_dir=args.store_config)

    if args.log:
        wap.set_logfile(args.log)

    if args.update:
        await wap.init_persister()
        logging.log("GREEN", "[*] Updating modules")
        attack_options = {"level": args.level, "timeout": args.timeout}
        wap.set_attack_options(attack_options)
        await wap.update(args.modules)
        sys.exit()

    try:
        for start_url in args.starting_urls:
            if start_url.startswith(("http://", "https://")):
                wap.add_start_url(Request(start_url))
            elif os.path.isfile(start_url):
                try:
                    with codecs.open(start_url, encoding="UTF-8") as urlfd:
                        for urlline in urlfd:
                            urlline = urlline.strip()
                            if urlline.startswith(("http://", "https://")):
                                wap.add_start_url(Request(urlline))
                except UnicodeDecodeError as exception:
                    logging.error("Error: File given with the -s option must be UTF-8 encoded !")
                    raise InvalidOptionValue("-s", start_url) from exception
            else:
                raise InvalidOptionValue('-s', start_url)

        for exclude_url in args.excluded_urls:
            if exclude_url.startswith(("http://", "https://")):
                wap.add_excluded_url(exclude_url)
            else:
                raise InvalidOptionValue("-x", exclude_url)

        if "proxy" in args:
            wap.set_proxy(args.proxy)

        if args.tor:
            wap.set_proxy("socks5://127.0.0.1:9050/")

        if "mitm_port" in args:
            wap.set_intercepting_proxy_port(args.mitm_port)

        wap.set_headless(args.headless)
        wap.set_wait_time(args.wait_time)

        if "cookie" in args:
            if os.path.isfile(args.cookie):
                wap.set_cookie_file(args.cookie)
            elif args.cookie.lower() in ("chrome", "firefox"):
                wap.load_browser_cookies(args.cookie)
            else:
                raise InvalidOptionValue("-c", args.cookie)

        if args.drop_set_cookie:
            wap.set_drop_cookies()

        if "http_credentials" in args:
            if "%" in args.http_credential:
                username, password = args.http_credential.split("%", 1)
                wap.set_http_credentials(HttpCredential(username, password, args.auth_method))
            else:
                raise InvalidOptionValue("-a", args.http_credential)

        for bad_param in args.excluded_parameters:
            wap.add_bad_param(bad_param)

        wap.set_max_depth(args.depth)
        wap.set_max_files_per_dir(args.max_files_per_dir)
        wap.set_max_links_per_page(args.max_links_per_page)
        wap.set_scan_force(args.scan_force)
        wap.set_max_scan_time(args.max_scan_time)
        wap.set_max_attack_time(args.max_attack_time)

        # should be a setter
        wap.verbosity(args.verbosity)
        if args.detailed_report:
            wap.set_detail_report()
        if args.color:
            wap.set_color()
        wap.set_timeout(args.timeout)
        wap.set_modules(args.modules)

        if args.no_bugreport:
            wap.set_bug_reporting(False)

        if "user_agent" in args:
            wap.add_custom_header("User-Agent", args.user_agent)

        for custom_header in args.headers:
            if ":" in custom_header:
                hdr_name, hdr_value = custom_header.split(":", 1)
                wap.add_custom_header(hdr_name.strip(), hdr_value.strip())

        if "output" in args:
            wap.set_output_file(args.output)

        if args.format not in GENERATORS:
            raise InvalidOptionValue("-f", args.format)

        wap.set_report_generator_type(args.format)

        wap.set_verify_ssl(bool(args.check_ssl))

        attack_options = {
            "level": args.level,
            "timeout": args.timeout,
            "tasks": args.tasks,
            "headless": wap.headless_mode,
        }

        if "dns_endpoint" in args:
            attack_options["dns_endpoint"] = args.dns_endpoint

        if "endpoint" in args:
            endpoint = fix_url_path(args.endpoint)
            if is_valid_endpoint('ENDPOINT', endpoint):
                attack_options["external_endpoint"] = endpoint
                attack_options["internal_endpoint"] = endpoint
            else:
                raise InvalidOptionValue("--endpoint", args.endpoint)

        if "external_endpoint" in args:
            external_endpoint = fix_url_path(args.external_endpoint)
            if is_valid_endpoint('EXTERNAL ENDPOINT', external_endpoint):
                attack_options["external_endpoint"] = external_endpoint
            else:
                raise InvalidOptionValue("--external-endpoint", external_endpoint)

        if "internal_endpoint" in args:
            internal_endpoint = fix_url_path(args.internal_endpoint)
            if is_valid_endpoint('INTERNAL ENDPOINT', internal_endpoint):
                if ping(internal_endpoint):
                    attack_options["internal_endpoint"] = internal_endpoint
                else:
                    logging.error("Error: Internal endpoint URL must be accessible from Wapiti!")
                    raise InvalidOptionValue("--internal-endpoint", internal_endpoint)
            else:
                raise InvalidOptionValue("--internal-endpoint", internal_endpoint)

        if args.skipped_parameters:
            attack_options["skipped_parameters"] = set(args.skipped_parameters)

        wap.set_attack_options(attack_options)

        await wap.init_persister()
        if args.flush_attacks:
            await wap.flush_attacks()

        if args.flush_session:
            await wap.flush_session()

    except InvalidOptionValue as msg:
        logging.error(msg)
        sys.exit(2)

    assert os.path.exists(wap.history_file)

    if "http_credentials" in args:
        if not await check_http_auth(wap.crawler_configuration):
            logging.warning("[!] HTTP authentication failed, a 4xx status code was received")
            return

    form_credential = None
    if "form_credentials" in args:
        # If the option is set it MUST have valid requirements
        if "%" not in args.form_credentials:
            raise InvalidOptionValue("--form-cred", args.http_credential)

        if "form_url" not in args:
            raise InvalidOptionValue("--form-url", "This option is required when --form-cred is used")

        username, password = args.form_credentials.split("%", 1)
        form_credential = FormCredential(
            username,
            password,
            args.form_url,
        )

    if "form_script" in args:
        await load_form_script(
            args.form_script,
            wap.crawler_configuration,
            form_credential,  # Either None or filled
            wap.headless_mode
        )
    elif "form_data" in args:
        if "form_url" not in args:
            raise InvalidOptionValue("--form-url", "This option is required when --form-data is used")

        raw_credential = RawCredential(
            args.form_data,
            args.form_url,
            args.form_enctype
        )
        await login_with_raw_data(wap.crawler_configuration, raw_credential)
    elif form_credential:
        is_logged_in, form, excluded_urls = await async_try_form_login(
            wap.crawler_configuration,
            form_credential,
            wap.headless_mode,
        )
        wap.set_auth_state(is_logged_in, form, form_credential.url)
        for url in excluded_urls:
            wap.add_excluded_url(url)

    loop = asyncio.get_event_loop()

    try:
        if not args.skip_crawl:
            if await wap.have_attacks_started() and not args.resume_crawl:
                pass
            else:
                if await wap.has_scan_started():
                    logging.info("[*] Resuming scan from previous session, please wait")

                await wap.load_scan_state()
                loop.add_signal_handler(signal.SIGINT, inner_ctrl_c_signal_handler)
                await wap.browse(global_stop_event, parallelism=args.tasks)
                loop.remove_signal_handler(signal.SIGINT)
                await wap.save_scan_state()

        if args.max_parameters:
            count = await wap.persister.remove_big_requests(args.max_parameters)
            logging.info(
                f"[*] {count} URLs and forms having more than {args.max_parameters} parameters were removed."
            )

        logging.info(f"[*] Wapiti found {await wap.count_resources()} URLs and forms during the scan")
        loop.add_signal_handler(signal.SIGINT, stop_attack_process)
        await wap.attack(global_stop_event)
        loop.remove_signal_handler(signal.SIGINT)

    except OperationalError:
        logging.error(
            "[!] Can't store information in persister. SQLite database must have been locked by another process"
        )
        logging.error("[!] You should unlock and launch Wapiti again.")
    except SystemExit:
        pass


def wapiti_asyncio_wrapper():
    asyncio.run(wapiti_main())
