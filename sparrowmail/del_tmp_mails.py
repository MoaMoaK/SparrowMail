# -*- coding: utf-8 -*-

import sqlite3
import time
import sys

from datetime import datetime
from sparrowmail import app, log, connect_db
from sparrowmail.scripts import postfix, dovecot, sieve

def update_postfix_mails() :
    """Get all mails info and trigger the postfix.update function with it"""
    
    db = connect_db()
                    
    cur = db.execute('SELECT m1.address as a1, m2.address as a2 FROM mails as m1 JOIN mails as m2 ON m1.target_id=m2.id OR m1.target_id ISNULL AND m1.address=m2.address')
    aliases_dict = cur.fetchall()
    aliases_list = [ (a['a1'], a['a2']) for a in aliases_dict ]

    cur = db.execute('SELECT address FROM mails WHERE target_id ISNULL')
    mailboxes_dict = cur.fetchall()
    mailboxes_list = [ m['address'] for m in mailboxes_dict ]

    db.close()

    result = postfix.update(app.config['ALIASES_FILE_PATH'],
            app.config['MAILBOXES_FILE_PATH'], aliases_list, mailboxes_list )
    if not result[0] :
        log( 'update_postfix_mails : '+result[1], level='ERROR' )
        return result[0]
        
    result = dovecot.remove_unexisting( app.config['PASSWD_FILE_PATH'], mailboxes_list )
    if not result[0] :
        log( 'update_postfix_mails : '+result[1], level='ERROR' )
        return result[0]

    return result[0]

def del_mails() :
    """Get a list of mails to delete because the end_date is passed"""

    log( '==> Starting to delete outdated temporary mails <==' )

    db = connect_db()
    cur = db.execute( 'SELECT id, address, target_id FROM mails WHERE end_date < CURRENT_TIMESTAMP' )
    to_del = cur.fetchall()

    success = True
    
    for m in to_del :
        try :
            db.execute( 'DELETE FROM mails WHERE id=?', [m['id']] )
            db.commit()
        except :
            log( 'Error while deleting '+m['address']+' from the database' )
            log( sys.exc_info(), level='ERROR')
            success = False
        else :
            log( 'Successfully deleted '+m['address'] )
    if len( to_del ) <= 0 :
        log( 'Nothing to delete' )

    db.close()

    if not success :
        log( 'Not updating postfix because an error occured previously' )
    elif not update_postfix_mails() :
        log( 'Something went wrong while updating postfix. Check the logs for more details.', level='ERROR' )
    log( '==> Ending deletion of outdated temporary mails <==' )

del_mails()
