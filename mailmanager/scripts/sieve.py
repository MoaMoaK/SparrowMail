# -*- coding: utf-8 -*-

import subprocess
import os


def get_filter_list( mail_dir_path, sieve_filename, exclude_dirname=[] ) :
    """Return a dict where each key is a mailbox associated with the sieve files
    mail_dir_path is the path where vmail starts
    sieve_filename is the base name of the sieve file we're looking for
    exclude_dirnames is a list of directories to exclude for search"""

    res = {}

    data_lvl1 = os.walk( mail_dir_path )
    dirname_lvl1, dirnames_lvl1, filenames_lvl1 = data_lvl1

    # for each directory (=domain) in the vmail dir
    for domain in dirnames_lvl1 :
        # exclude dir that are not actual domains
        if domain in exclude_dirname :
            continue
        
        data_lvl2 = os.walk( os.path.join( dirname_lvl1, domain) )
        dirname_lvl2, dirnames_lvl2, filenames_lvl2 = data_lvl2

        # For each directory (=user) in this domain
        for user in dirnames_lvl2 :
            # Exclude dir that are not actual users
            if user in exclude_dirname :
                continue

            data_lvl3 = os.walk( os.path.join( dirname_lvl2, user) )
            dirname_lvl3, dirnames_lvl3, filenames_lvl3 = data_lv3
            
            # Add this to res variable even if it doesn't exists
            res[user+'@'+domain] = os.path.join( dirname_lvl3, sieve_filename )

    # And return the results
    return res


def get_filter_filepath_from_mailbox( mail_dir, mailbox, sieve_filename ) :
    """Retrieve the sieve file associated with a mailbox"""

    # Get info from mailbox
    user, domain = mialbox.split( '@' )
    # Return the associated sieve file path
    return os.path.join( mail_dir_path, domain, user, sieve_filename )


def get_filter_content_from_filepath( filepath ):
    """Return the data inside the sieve file given"""

    f = open( filepath, 'r' )

    # Warning if file is bigger than memory can be dangerous
    # max size read should be specified in f.read( size )
    content = f.read()

    return content


def get_filter_content_from_mailbox( mail_dir_path, mailbox, sieve_filename ) :
    """Return the data inside the sieve file associated with the mailbox given"""

    # Get the associated sieve file path
    filepath = get_filter_filepath_from_mailbox( mail_dir_path, mailbox, sieve_filename )
    # Get the content
    return get_filter_content_from_filepath( filepath )


def set_filter_from_filepath( filepath, content ) :
    """Write data inside the sieve file given"""

    f = open( filepath, 'w' )

    # Write the actual content
    f.write( content )


def set_filter_from_mailbox( mail_dir_path, mailbox, sieve_filename, content ) :
    """Write data inside the sieve file associated with mailbox given"""

    # Get the associated sieve file path
    filepath = get_filter_filepath_from_mailbox( mail_dir_path, mailbox, sieve_filename )
    # Write the content
    set_filter_from_filepath( filepath, content )




