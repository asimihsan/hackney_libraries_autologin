# hackney_libraries_autologin

## Introduction

CLR James library offers free Wi-Fi. However, every hour my Mac gets booted off; I suspect they either require explicit re-login to demonstrate client liveliness or just don't support Macs.

This tool logs into their web portal when needed; your connection will die for on average 10 seconds before the tool kicks in.

## Requirements

-	Python with [pip](http://www.pip-installer.org/en/latest/installing.html).
-	(optional, recommended) install [virtualenv](http://www.virtualenv.org/en/latest/index.html) and [virtualenvwrapper](http://www.doughellmann.com/projects/virtualenvwrapper/).

## Quickstart

-	Clone the repo.
-	(if you installed virtualenv and virtualenvwrapper):
	-	`mkvirtualenv hackney_libraries_autologin`
	-	`workon hackney_libraries_autologin`
-	`pip install -r requirements.txt`
-	Launch the `Keychain Access` application.
-	Add a new account called `Hackney Libraries`.
	-	Set the username field to your library card's number.
	-	Set the password to your PIN.
-	Quit the `Keychain Access` application.
-	Execute `./src/auto_login.py`.

## How it works

-	Use the `airport` command-line utility to confirm that we are both connected to a Wi-Fi network and that the Wi-Fi network's SSID is `LBH-Libraries`.
-	If the above is true, determine if we need to re-login by attempting to HTTP GET `http://www.pip-installer.org/en/latest/installing.html`; it times out if we don't need to log in, and redirects to a login page if we do need to log in.
-	If we need to log in, HTTP POST to `http://www.pip-installer.org/en/latest/installing.html` with appropriate `x-url-form-encoded` content, cookies, and referrer.
-	We get the credentials directly from `Keychain Access` by executing `security`.

That should be enough instructions to modify the script if need be; consult the top-most section titled `Constants` for stuff to chain if need be.