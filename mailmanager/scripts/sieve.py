# -*- coding: utf-8 -*-

import subprocess
import os
import string
import random


def get_filter_list( mail_dir_path, sieve_filename, exclude_dirname=[] ) :
    """Return a dict where each key is a mailbox associated with the sieve files
    mail_dir_path is the path where vmail starts
    sieve_filename is the base name of the sieve file we're looking for
    exclude_dirnames is a list of directories to exclude for search"""

    res = {}

    entries_lvl1 = os.listdir( mail_dir_path )

    # for each directory (=domain) in the vmail dir
    for domain in entries_lvl1 :
        # Get absolute path
        abspath_lvl2 = os.path.join( mail_dir_path, domain )

        # Exclude files
        if os.path.isfile( abspath_lvl2 ) :
            continue
        # Exclude dir that are not actual domains or that are files
        if domain in exclude_dirname :
            continue
        
        entries_lvl2 = os.listdir( abspath_lvl2 )

        # For each directory (=user) in this domain
        for user in entries_lvl2 :
            # Get absolute path
            abspath_lvl3 = os.path.join( abspath_lvl2, user )

            # Exclude files
            if os.path.isfile( abspath_lvl3 ) :
                continue
            # Exclude dir that are not actual users
            if user in exclude_dirname :
                continue

            # Add this to res variable even if it doesn't exists
            res[user+'@'+domain] = os.path.join( abspath_lvl3, sieve_filename )

    # And return the results
    return res


def get_filter_filepath_from_mailbox( mail_dir_path, mailbox, sieve_filename ) :
    """Retrieve the sieve file associated with a mailbox"""

    # Get info from mailbox
    user, domain = mailbox.split( '@' )
    # Return the associated sieve file path
    return os.path.join( mail_dir_path, domain, user, sieve_filename )


def get_filter_content_from_filepath( filepath ):
    """Return the data inside the sieve file given"""

    try :
        with open( filepath, 'r' ) as f:
            # Warning if file is bigger than memory can be dangerous
            # max size read should be specified in f.read( size )
            content = f.read()
    except IOError :
        content = ""


    return content


def get_filter_content_from_mailbox( mail_dir_path, mailbox, sieve_filename ) :
    """Return the data inside the sieve file associated with the mailbox given"""

    # Get the associated sieve file path
    filepath = get_filter_filepath_from_mailbox( mail_dir_path, mailbox, sieve_filename )
    # Get the content
    return get_filter_content_from_filepath( filepath )


def set_filter_from_filepath( filepath, content ) :
    """Write data inside the sieve file given"""

    # Check for the dir to exists
    dir_path = os.path.dirname( filepath )
    if not os.path.exists( dir_path ) :
        os.makedirs( dir_path )

    # Open the file and create it if it doesn't exists
    with open( filepath, 'w+' ) as f :
        # Write the actual content
        .write( content )


def set_filter_from_mailbox( mail_dir_path, mailbox, sieve_filename, content ) :
    """Write data inside the sieve file associated with mailbox given"""

    # Get the associated sieve file path
    filepath = get_filter_filepath_from_mailbox( mail_dir_path, mailbox, sieve_filename )
    # Write the content
    set_filter_from_filepath( filepath, content )


def check_filter_content( content ) :
    """Write the content to a temporary file and check if it can compile it
    If there are errors return it in second element of the returned tuple"""
    
    # Get a random file in /tmp
    characters = string.ascii_letters + string.digits
    filename = ''.join([random.choice( characters ) for n in range( 10 )])
    dir_path = '/tmp/mailmanager/'
    if not os.path.exists( dir_path ) :
        os.makedirs( dir_path )
    sievefile_path = dir_path + filename + '.sieve'
    svbinfile_path = dir_path + filename + '.svbin'

    with open( sievefile_path, 'w+' ) as f :
        # Write the data in tmp file
        f.write( content )

    # Try to compile
    try :
        subprocess.check_output(['sievec', '-d', sievefile_path, svbinfile_path], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print e.output
        return (False, e.output.replace( filename+':', "" ).split( '\n' )[:-2])
    else :
        return (True, None)



