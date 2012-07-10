#!/usr/bin/env python

import os
import sys
import requests
import subprocess
import time
import re
import select

# -----------------------------------------------------------------------------
#   Constants.
# -----------------------------------------------------------------------------
APP_NAME = "auto_login"
LOG_FILENAME = os.path.join(__file__, os.pardir, os.pardir, "logs", "%s.log" % APP_NAME)
CHECK_INTERVAL = 10
LOGIN_INITIAL_URI = r"https://securelogin.arubanetworks.com/"
LOGIN_POST_URI =    r"https://securelogin.arubanetworks.com/cgi-bin/login"
KEYCHAIN_ACCOUNT_NAME = "Hackney Library"
COMMAND_GET_CREDENTIALS = "security find-generic-password -g -s '%s'" % KEYCHAIN_ACCOUNT_NAME
COMMAND_GET_WIFI = r"/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I"
DESIRED_SSID = "LBH-Libraries"
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
#   Logging.
# -----------------------------------------------------------------------------
import logging
import logging.handlers
logger = logging.getLogger(APP_NAME)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

log_directory = os.path.abspath(os.path.join(LOG_FILENAME, os.pardir))
if not os.path.isdir(log_directory):
    os.makedirs(log_directory)
fh = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=10*1024*1024, backupCount=10)
fh.setFormatter(formatter)
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)
# -----------------------------------------------------------------------------

def is_login_required():
    logger = logging.getLogger("%s.is_login_required" % APP_NAME)
    logger.debug("entry.")

    if get_wifi_ssid() != DESIRED_SSID:
        logger.debug("We're not on the DESIRED_SSID.")
        return None
    try:
        request = requests.get(LOGIN_INITIAL_URI, timeout=3)
    except requests.exceptions.ConnectionError:
        logger.warning("connection error.")
        return None
    except requests.exceptions.Timeout:
        logger.warning("timeout on getting LOGIN_INITIAL_URL")
        return None
    if len(request.history) > 0:
        logger.debug("previous request might have resulted in a redirect")
        if request.history[0].status_code == 302 and request.history[0].url == LOGIN_INITIAL_URI:
            logger.debug("previous request redirected. login is required")
            return (True, request)
    return None

def get_wifi_ssid():
    logger = logging.getLogger("%s.get_wifi_ssid" % APP_NAME)
    logger.debug("entry.")

    # -------------------------------------------------------------------------
    #   Execute command that gets wifi information
    # -------------------------------------------------------------------------
    proc = subprocess.Popen(COMMAND_GET_WIFI,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    (stdout, stderr) = proc.communicate()
    output = '\n'.join([stdout, stderr])
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    #   Get SSID.
    # -------------------------------------------------------------------------
    m = re.search(".*SSID: (?P<ssid>.*?)\n", output, re.DOTALL)
    if not m:
        logger.error("failed to find ssid in output.")
        return None
    ssid = m.groupdict()['ssid']
    logger.debug("ssid: %s" % ssid)
    # -------------------------------------------------------------------------

    return ssid

def login(previous_request, username, password):
    logger = logging.getLogger("%s.login" % APP_NAME)
    logger.debug("entry. previous_request.url: %s, username: %s" % (previous_request.url, username))
    headers = {"Referer": previous_request.url}
    data = {"user": username,
            "password": password,
            "cmd": "authenticate",
            "Login": "Log In"}
    request = requests.post(LOGIN_POST_URI,
                            data=data,
                            headers=headers,
                            cookies=previous_request.cookies)
    logger.debug("request: %s" % request)

def get_username_and_password():
    logger = logging.getLogger("%s.get_username_and_password" % APP_NAME)
    logger.debug("entry.")

    # -------------------------------------------------------------------------
    #   Execute command that gets username and password.
    # -------------------------------------------------------------------------
    proc = subprocess.Popen(COMMAND_GET_CREDENTIALS,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    (stdout, stderr) = proc.communicate()
    output = '\n'.join([stdout, stderr])
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    #   Get username.
    # -------------------------------------------------------------------------
    m = re.search(".*\"acct\".*?\"(?P<username>.*?)\"", output, re.DOTALL)
    if not m:
        logger.error("failed to find acct in output.")
        return None
    username = m.groupdict()['username']
    logger.debug("username: %s" % username)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    #   Get password.
    # -------------------------------------------------------------------------
    m = re.search(".*password: \"(?P<password>.*?)\"", output, re.DOTALL)
    if not m:
        logger.error("failed to find password in output.")
        return None
    password = m.groupdict()['password']
    # -------------------------------------------------------------------------

    return (username, password)

def wait_for_any_input(timeout):
    logger = logging.getLogger("%s.wait_for_any_input" % APP_NAME)
    r_list, _, _ = select.select([sys.stdin], [], [], timeout)
    if r_list:
        sys.stdin.read(1)
        return True
    else:
        return False

def main():
    logger = logging.getLogger("%s.main" % APP_NAME)
    logger.debug("entry.")
    last_checked_time = 0
    while True:
        if time.time() - last_checked_time > CHECK_INTERVAL:
            logger.debug("login might be required...")
            rv = is_login_required()
            if rv:
                logger.debug("login is required.")
                (_, request) = rv
                (username, password) = get_username_and_password()
                login(request, username, password)

            last_checked_time = time.time()
        if wait_for_any_input(1):
            logger.debug("user input, so check immediately")
            last_checked_time = 0

if __name__ == "__main__":
    main()
