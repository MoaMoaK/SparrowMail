# SparrowMail

[![build status](https://gitlab.rez-rennes.fr/moamoak/sparrowmail/badges/master/build.svg)](https://gitlab.rez-rennes.fr/moamoak/sparrowmail/commits/master)

## Introduction

SparrowMail is a web app written in python using [the framework Flask](http://flask.pocoo.org).  
The project goal is to be able to manage mails through a web interface such as quickly adding new mailboxes or edit filters for each mailbox.  
The project is currently designed for use with [postfix](http://www.postfix.org/) (configured with virtual user), [dovecot](https://dovecot.org/) and [pigeonhole](https://pigeonhole.dovecot.org/) (a dovecot plugin for sieve filters).

---

This project has been written by [Maël "MoaMoaK" Kervella](https://www.maelkervella.eu)

## List of features

  * Mailboxes and aliases managed through a database
    * Add mailboxes and aliases
    * Delete mailboxes and aliases
    * Mailboxes and aliases can have a time limit
    * When time limit is reached, mail account is deactivated (not deleted)
    * Edit options of mailboxes (time limit and password) and aliases (time limit)
  * Users are also maanged through the database
    * User created upon installation
    * Edit options for the user (username, password)7
  * Connection is mandatory for seeing any infos or any modification
    * Password are salted and hashed inside the database of course
  * Sieve filter can be edited for each mailbox
    * Syntax verification before each sieve filter modification

## Installation

The installation is meant to be quick and easy.  
Simply clone the git repository where you want it to be installed :  
`git clone https://moamoak@gitlab.rez-rennes.fr/moamoak/sparrowmail.git`  
And install it using pip :  
`pip install sparrowmail`

## Configuration

All needed configuration is located in `<install_path>/sparrowmail/config.py`.  
See comments and default values for signification of each parameter.
