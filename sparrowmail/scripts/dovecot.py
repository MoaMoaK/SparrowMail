# -*- coding: utf-8 -*-

import subprocess

def add_passwd( passwd_file_path, address, pw ) :
    """Add a mail_address:hased_password line into the password file"""

    with open( passwd_file_path, 'a' ) as f :
        # Hash the password and write it in file
        hashed_passwd = subprocess.check_output(['doveadm', 'pw', '-s', 'SSHA512', '-p', pw])
        f.write(address+':'+hashed_passwd)

    return reload_dovecot()


def check_passwd( passwd_file_path, address, pw ) :
    """Check if the given password match the existing one"""

    with open( passwd_file_path, 'r') as f :
        lines = f.readlines()

    # Search for the line about this address
    for line in lines :
        # Is it the right line ?
        if line.startswith(address) :
            # Get the hashed password
            hashed_passwd = line.split(':')[-1]
            # And check if it matches the given password
            try :
                output = subprocess.check_output(
                        ['doveadm', 'pw', '-p', pw, '-t', hashed_passwd])
            except subprocess.CalledProcessError :
                # If the doveadm test failed
                return False
            else :
                # If the doveadm test succeded
                return True
    
    # Address not found in the passwd file
    return False

def change_passwd( passwd_file_path, address, pw ) :
    """Change the password associated with the given address. Don't create new entry if don't exists"""

    with open( passwd_file_path, 'r') as f :
        lines = f.readlines()

    # Search for the line about this address
    for i in range(len(lines)) :
        # Is it the right line ?
        if lines[i].startswith(address) :
            # Hash the password nad write it
            hashed_passwd = subprocess.check_output(['doveadm', 'pw', '-s', 'SSHA512', '-p', pw])
            lines[i] = address+':'+hashed_passwd+'\n'
    
    with open( passwd_file_path, 'w') as f :
        f.writelines( lines )

    return reload_dovecot()

def reload_dovecot() :
    """"Start a subprocess to reload dovecot and take the new configuration into account"""

    try :
        subprocess.check_output(
                ['systemctl', 'reload', 'dovecot'] )
    except subprocess.CalledProcessError as e :
        return (False, e.ouput)
    else :
        return (True, None)
