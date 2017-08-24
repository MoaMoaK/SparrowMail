# -*- coding: utf-8 -*-

import subprocess

def add_passwd(passwd_file_path, address, pw) :
    f = open(passwd_file_path, 'a')

    hashed_passwd = subprocess.check_output(['doveadm', 'pw', '-s', 'SSHA512', '-p', pw])
    f.write(address+':'+hashed_passwd)
