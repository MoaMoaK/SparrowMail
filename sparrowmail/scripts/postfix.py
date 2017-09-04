# -*- coding: utf-8 -*-

import subprocess

def reload_postfix () :
    try :
        subprocess.check_output(['sudo', '/etc/init.d/postfix', 'reload'])
    except subprocess.CalledProcessError as e :
        return (False, e.output)
    else :
        return (True, None)

def hash_file (file_path) :
    try :
        subprocess.check_output(['postmap', file_path])
    except subprocess.CalledProcessError as e :
        return (False, e.output)
    else :
        return (True, None)

def update_aliases( aliases_file_path, aliases_list ) :
    with open( aliases_file_path, 'w' ) as f :
        for alias in aliases_list :
            f.write( alias[0]+' '+alias[1]+'\n' )

    return hash_file( aliases_file_path )


def update_mailboxes( mailboxes_file_path, mailboxes_list ) :
    with open( mailboxes_file_path, 'w' ) as f :
        for mailbox in mailboxes_list :
            f.write( mailbox+' '+mailbox+'\n' )

    return hash_file( mailboxes_file_path )


def update (aliases_file_path, mailboxes_file_path, aliases_list, mailboxes_list) :
    
    res = update_aliases (aliases_file_path, aliases_list)
    if not res[0] :
        return res

    res = update_mailboxes (mailboxes_file_path, mailboxes_list)
    if not res [0] :
        return res

    return reload_postfix()
