# -*- coding: utf-8 -*-    

###################################################################
## Config File for MailManager                                   ##
## All relative path starts from the root dir of the application ##
###################################################################



## Security Warning
## Those options should be set to False
## if not in development environnement
DEBUG = True
TESTING = False



## Main database

# -> Where the database is store
DATABASE = 'mailmanager/db/mailmanager.db'
# ->
SECRET_KEY = 'development-key'



## Files for postfix virtual accounts

# -> aliases associations 
#    in postix conf : virtual_alias_map
ALIASES_FILE_PATH = '/tmp/aliases'

# -> mailboxes addresses
#    in postfix conf : virtual_mailbox_maps
MAILBOXES_FILE_PATH = '/tmp/mailboxes'



## Files for dovecot management

# -> mailboxes passwords
#    in dovecot conf : passdb { args = username_format=%u scheme=ssha512 <file> }
PASSWD_FILE_PATH = '/tmp/passwd.db'



## Sieve handling configuration

# -> Where the virtual mailboxes are stored
#    Tree must look like <VMAIL_DIR>/<domain>/<user>/mail/{cur|new|tmp}
VMAIL_DIR = '/tmp/vmail'

# -> List of directories to exclude when exploring the virtual mailboxes tree
#    because they are not assoicated with a domain or a user for example
EXCLUDE_DIRS = ['sieve-after', 'sieve-after']

# -> The name of the sieve files
#    in dovecot conf : plugin { sieve = <file> }
SIEVE_FILENAME = '.dovecot.sieve'

