# -*- coding: utf-8 -*-

import subprocess

def reload_postfix () :
    try :
        subprocess.check_output(['systemctl', 'reload', 'postfix'])
    except subprocess.CalledProcessError as e :
        return False
    else :
        return True

def hash_file (file_path) :
    try :
        subprocess.check_output(['postmap', file_path])
    except subprocess.CalledProcessError as e :
        return False
    else :
        return True

def update_aliases( aliases_file_path, aliases_list ) :
    f = open( aliases_file_path, 'w' )
    
    for alias in aliases_list :
        f.write( alias[0]+' '+alias[1]+'\n' )

    f.close()

    hash_file( aliases_file_path )


def update_mailboxes( mailboxes_file_path, mailboxes_list ) :
    f = open( mailboxes_file_path, 'w' )

    for mailbox in mailboxes_list :
        f.write( mailbox+' '+mailbox+'\n' )

    f.close()

    hash_file( mailboxes_file_path )


def update (aliases_file_path, mailboxes_file_path, aliases_list, mailboxes_list) :
    update_aliases (aliases_file_path, aliases_list)
    update_mailboxes (mailboxes_file_path, mailboxes_list)
    reload_postfix()
