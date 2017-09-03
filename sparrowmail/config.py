# -*- coding: utf-8 -*-    

###################################################################
## Config File for SparrowMail                                   ##
## All relative path starts from the root dir of the application ##
###################################################################



## Flask configuration ##
#########################
#   Debugging options
#   /!\ Security Warning not use those in dev env
DEBUG = True
TESTING = False
EXPLAIN_TEMPLATE_LOADING = False
#   Secret key for encryption
SECRET_KEY = 'development-key'
#   Cookies configuration
SESSION_COOKIE_NAME = 'session'
SESSION_COOKIE_DOMAIN = 'mail.maelkervella.eu'
SESSION_COOKIE_PATH = '/'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False
SESSION_REFRESH_EACH_REQUEST = True
#   Server hostname and port
SERVER_NAME = 'mail.maelkervella.eu:5000'
#   Website root url
#   None if sub-domain is only used for SparrowMail
#   http{s|}://<SERVER_NAME>/<APPLICATION_ROOT> if not
APPLICATION_ROOT = None




## Main database ##
###################
#   Where the database is store
DATABASE = 'sparrowmail/db/sparrowmail.db'



## Files for postfix virtual accounts ##
########################################
#   aliases associations 
#   in postix conf : virtual_alias_map
ALIASES_FILE_PATH = '/tmp/aliases'
#   mailboxes addresses
#   in postfix conf : virtual_mailbox_maps
MAILBOXES_FILE_PATH = '/tmp/mailboxes'



## Files for dovecot management ##
##################################
#   mailboxes passwords
#   in dovecot conf : passdb { args = username_format=%u scheme=ssha512 <file> }
PASSWD_FILE_PATH = '/tmp/passwd.db'



## Sieve handling configuration ##
##################################
#   Where the virtual mailboxes are stored
#   Tree must look like <VMAIL_DIR>/<domain>/<user>/mail/{cur|new|tmp}
VMAIL_DIR = '/tmp/vmail'
#   List of directories to exclude when exploring the virtual mailboxes tree
#   because they are not assoicated with a domain or a user for example
EXCLUDE_DIRS = ['sieve-after', 'sieve-after']
#   The name of the sieve files
#   in dovecot conf : plugin { sieve = <file> }
SIEVE_FILENAME = '.dovecot.sieve'

