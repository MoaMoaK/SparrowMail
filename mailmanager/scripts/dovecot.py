# -*- coding: utf-8 -*-

import subprocess

def add_passwd(passwd_file_path, address, pw) :
    f = open(passwd_file_path, 'a')

    hashed_passwd = subprocess.check_output(['doveadm', 'pw', '-s', 'SSHA512', '-p', pw])
    f.write(address+':'+hashed_passwd)

def check_passwd( passwd_file_path, address, pw ) :
    """Check if the given password match the existing one"""

    f = open( passwd_file_path, 'r')

    # Search for the line about this address
    for line in f.readlines() :
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
