# -*- coding: utf-8 -*-

# Import PyPI packages
import os
import sys
import sqlite3
import time
from random import randint
from hashlib import sha256
from datetime import datetime
from exceptions import ValueError

# Import other packages
from email_validator import validate_email, EmailNotValidError

# Import flask packages
from flask import Flask, request, session, g, redirect, url_for, abort, \
             render_template, flash

# Import custom packages
from sparrowmail.scripts import postfix
from sparrowmail.scripts import dovecot
from sparrowmail.scripts import sieve
from sparrowmail.error import Error, WrongArg, MissingArg, DBManip, SieveManip, SieveSyntax, Hacker, Unknown, ConfPasswd

app = Flask(__name__) # create the application instance :)
app.config.from_object('sparrowmail.config') # load config from the config.py file

# Override config from an environment variable
app.config.from_envvar('SPARROWMAIL_SETTINGS', silent=True)

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def init_db():
    db = get_db()
    with app.open_resource('db/schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
        db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database. Meant to be used as a flask command."""
    init_db()
    log('Initialized the database.')

def initdb_python():
    """Initialize the database. Meant to be used in python scripts."""
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    with app.open_resource('db/schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
        db.commit()
    db.close()




def saltpassword (password, salt) :
    """Return a salted password with the algo sha256(passwd+salt)"""

    saltedpassword = password + str(salt)
    return sha256(saltedpassword.encode('utf-8')).hexdigest()


def log (message, level='INFO') :
    """Print a log formated message"""

    print(time.ctime() + ' ['+level+'] ' + str(message))
    return None


def update_postfix_mails() :
    """Get all mails info and trigger the postfix.update function with it"""

    db = get_db()
    
    cur = db.execute('SELECT m1.address as a1, m2.address as a2 FROM mails as m1 JOIN mails as m2 ON m1.target_id=m2.id OR m1.target_id ISNULL AND m1.address=m2.address')
    aliases_dict = cur.fetchall()
    aliases_list = [ (a['a1'], a['a2']) for a in aliases_dict ]

    cur = db.execute('SELECT address FROM mails WHERE target_id ISNULL')
    mailboxes_dict = cur.fetchall()
    mailboxes_list = [ m['address'] for m in mailboxes_dict ]

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

def add_dovecot_passwd( mailbox_add, pw ) :
    """Triggers the dovecot.update_passwd function with the right infos"""
    
    result = dovecot.add_passwd(app.config['PASSWD_FILE_PATH'], mailbox_add, pw)
    if not result[0] :
        log( 'add_dovecot_passwd : '+result[1], level='ERROR' )

    return result[0]

def check_dovecot_passwd( mailbox_add, pw ) :
    """Triggers the dovecot.check_passwd function with the right infos"""

    return dovecot.check_passwd(app.config['PASSWD_FILE_PATH'], mailbox_add, pw)

def change_dovecot_passwd( mailbox_add, pw ) :
    """Triggers the dovecot.change_passwd function with the right infos"""

    result = dovecot.change_passwd(app.config['PASSWD_FILE_PATH'], mailbox_add, pw)
    if not result[0] :
        log( 'change_dovecot_passwd : '+result[1], level='ERROR' )

    return result[0]

def get_sieve_filter_list( ) :
    """Trigger the sieve.get_filter_list function with the right infos"""

    return sieve.get_filter_list( app.config['VMAIL_DIR'],
            app.config['SIEVE_FILENAME'], app.config['EXCLUDE_DIRS'] )

def get_sieve_filter_content( mailbox ) :
    """Triggers the sieve.get_filter_content_from_mailbox with the right infos"""

    return sieve.get_filter_content_from_mailbox( app.config['VMAIL_DIR'],
            mailbox, app.config['SIEVE_FILENAME'] )

def set_sieve_filter_content( mailbox, content ) :
    """Triggers the sieve.set_filter_content_from_mailbox with the right infos"""

    result = sieve.set_filter_from_mailbox( app.config['VMAIL_DIR'],
            mailbox, app.config['SIEVE_FILENAME'], content )
    if not result[0] :
        log( 'set_sieve_filter_content : '+result[1], level='ERROR' )

    return result[0]

def check_sieve_filter_content( content ):
    """Triggers the sieve.check_filter_content with the right infos"""

    return sieve.check_filter_content( content )




@app.route('/', methods=['GET'])
def welcome():
    """The default welcome web page"""

    return render_template('welcome.html')

@app.route('/folders/', methods=['GET'])
def folders():
    """The folder web page"""

    return render_template('folders.html')
    
@app.route('/mails/', methods=['GET'])
def mails():
    """The web page presenting the different mail infos"""

    if not session.get('user_id') :
        return redirect( url_for( 'login', redir='mails' ) )

    # Get the mailboxes and aliases from database (mails = mailboxes + aliases)
    mails = []

    db = get_db()

    cur = db.execute('SELECT id, address, end_date FROM mails WHERE target_id ISNULL')
    mailboxes = cur.fetchall()

    for mailbox in mailboxes :
        cur = db.execute('SELECT id, address, end_date FROM mails WHERE target_id=?',
                [mailbox['id']])
        aliases = cur.fetchall()

        mails.append ({'address': mailbox['address'],
                        'id': mailbox['id'],
                        'end_date' : mailbox['end_date'],
                        'aliases' : aliases})

    return render_template('mails.html', mails=mails)



@app.route('/addalias/<int:mailbox_id>', methods=['GET', 'POST'])
def add_alias(mailbox_id):
    """The page to add 1 alias to a specific mailbox"""
    
    if not session.get('user_id') :
        return redirect( url_for( 'login', redir='mails' ) )

    # Get the address associated with the wanted id
    db = get_db()
    cur = db.execute('SELECT address FROM mails WHERE id=? AND target_id ISNULL', [mailbox_id])
    mailbox = cur.fetchone()

    # Is the mailbox_id valid ?
    if not mailbox :
        flash ('The mailbox you\'ve asked to add an alias to doesn\'t exist')
        return redirect(url_for('welcome'))
    
    # Possible errors
    errors = []

    # Has the user filled the form ?
    if request.method == 'POST' :
        # Is the field not empty
        if not request.form.get('alias') :
            errors.append( Error( MissingArg,
                'The alias field can\'t be empty' ) )
        else :
            try :
                # Get the date limit if there is one
                end_date=None
                if request.form.get('end') :
                    end_str = "-".join([request.form.get(select).zfill(2) for select in ['endyear', 'endmonth', 'endday', 'endhour', 'endmin', 'endsec']])
                    end_date=datetime.strptime(end_str, "%Y-%m-%d-%H-%M-%S")

                # Is it a valid email ?
                v = validate_email(request.form.get('alias'))
                new_alias = v['email']
                # If no exceptions so far, let's update the db
                db.execute('INSERT INTO mails (address, target_id, end_date) VALUES (?, ?, ?)',
                        [new_alias, mailbox_id, end_date])
                db.commit()

                if not update_postfix_mails() :
                    errors.append( Error( PostfixManip,
                        'Something went wrong while updating postfix. Check the logs for more details.' ) )

            except EmailNotValidError :
                # Only exception from validate_email (= email not valid )
                errors.append( Error( WrongArg,
                    request.form.get('alias')+' is not a valid email' ) )
                log (sys.exc_info(), level='ERROR')
            except sqlite3.OperationalError :
                # Exceptions about database request
                errors.append( Error( DBManip,
                    'Something went wrong while updating the database' ) )
                log (sys.exc_info(), level='ERROR')
            except sqlite3.IntegrityError :
                # Exceptions about integrity of database probably unique constraint
                errors.append( Error( WrongArg,
                    'This mail address is already used, try another one' ) )
                log (sys.exc_info(), level='ERROR')
            except ValueError :
                # Exceptions about datetime wrong value
                errors.append( Error( Hacker,
                    'Please don\'t even try to mess up with the form' ) )
                log (sys.exc_info(), level='ERROR')
            except :
                # Other excpetions
                errors.append( Error( Unknown,
                    'Something went wrong' ) )
                log (sys.exc_info(), level='ERROR')
            else :
                # Everyting is ok, notify the user about success and go back to welcome page
                log ('Alias '+new_alias+' added to '+mailbox['address'])
                flash (new_alias+' has been successfully added as an alias')
                return redirect(url_for('mails'))

    # If GET method used or
    # In case of something wrong, go back to the form with the error displayed
    return render_template('addalias.html', errors=errors, mailbox_address=mailbox['address'])




@app.route('/addmailbox', methods=['GET', 'POST'])
def add_mailbox():
    """The page to add 1 mailbox"""
    
    if not session.get('user_id') :
        return redirect( url_for( 'login', redir='mails' ) )

    # Possible errors
    errors = []

    # Has the user filled the form ?
    if request.method == 'POST' :
        # Is the mailbox field not empty
        if not request.form.get('mailbox') :
            errors.append( Error( MissingArg,
                    'The mailbox field can\'t be empty' ) )
        # Are the password fields not empty
        elif not request.form.get('password1') or not request.form.get('password2'):
            errors.append( Error( MissingArg,
                'Please fill in the password fields' ) )
        elif request.form.get('password1') != request.form.get('password2'):
            errors.append( Error( WrongArg,
                'Password don\'t match' ) )
        else :
            try :
                # Get the date limit if there is one
                end_date=None
                if request.form.get('end') :
                    end_str = "-".join([request.form.get(select).zfill(2) for select in ['endyear', 'endmonth', 'endday', 'endhour', 'endmin', 'endsec']])
                    end_date=datetime.strptime(end_str, "%Y-%m-%d-%H-%M-%S")

                # Is it a valid email ?
                v = validate_email(request.form.get('mailbox'))
                new_mailbox = v['email']

                # If no exceptions so far, let's update the db
                db = get_db()
                db.execute('INSERT INTO mails (address, end_date) VALUES (?, ?)',
                        [new_mailbox, end_date])
                db.commit()

                # Update the mailboxes files
                if not update_postfix_mails() :
                    errors.append( Error( PostfixManip,
                        'Something went wrong while updating postfix. Check the logs for more details.' ) )
                # Update the password file
                elif not add_dovecot_passwd(new_mailbox, request.form.get('password1')) :
                    errors.append( Error( DovecotManip,
                        'Something went wrong while setting the password. Check the logs for more details.' ) )

            except EmailNotValidError :
                # Only exception from validate_email (= email not valid )
                errors.append( Error( WrongArg,
                    request.form.get('mailbox')+' is not a valid email' ) )
                log (sys.exc_info(), level='ERROR')
            except sqlite3.OperationalError :
                # Exceptions about database
                errors.append( Error( DBManip,
                    'Something went wrong while updating the database' ) )
                log (sys.exc_info(), level='ERROR')
            except sqlite3.IntegrityError :
                # Exceptions about integrity of database probably unique constraint
                errors.append( Error( WrongArg,
                    'This mail address is already used, try another one' ) )
                log (sys.exc_info(), level='ERROR')
            except ValueError :
                # Exceptions about datetime wrong value
                errors.append( Error( Hacker,
                    'Please don\'t even try to mess up with the form' ) )
                log (sys.exc_info(), level='ERROR')
            except :
                # Other exceptions
                errors.append( Error( Unknown,
                    'Something went wrong' ) )
                log (sys.exc_info(), level='ERROR')
                raise
            else :
                # Everyting is ok, notify the user about success and go back to mails page
                log ('Mailbox '+new_mailbox+' added')
                flash (new_mailbox+' has been successfully added as a mailbox')
                return redirect(url_for('mails'))
    
    # If GET method used or
    # In case of something wrong, go back to the form with the error displayed
    return render_template('addmailbox.html', errors=errors)

@app.route('/editalias/<int:alias_id>', methods=['GET', 'POST'])
def edit_alias(alias_id) :
    """The web page to edit an alias informations"""

    if not session.get('user_id') :
        return redirect( url_for( 'login', redir='mails' ) )

    # Get some info about the alias asked to be edited
    db = get_db()
    cur = db.execute('SELECT address, target_id, end_date FROM mails WHERE id=?', [alias_id])
    alias = cur.fetchone()

    # Does the alias exists or is it not an alias ?
    if not alias or not alias['target_id']:
        flash( 'The alias asked to be deleted doesn\'t exists or is not an alias' )
        return redirect( url_for( 'mails' ) )

    # Possible errors
    errors = []

    # Has the user filled in the form ?
    if request.method == 'POST' :
        # Is the old_password field not empty
        if not request.form.get( 'old_password' ) :
            errors.append( Error( ConfPasswd,
                "You must fill in the password field to be able to modify anything" ) )

        else :
            # Get info about the associated mailbox
            cur = db.execute('SELECT address FROM mails WHERE id=?', [alias['target_id']])
            associated_mailbox = cur.fetchone()

            # Any strange error ?
            if not associated_mailbox :
                errors.append( Error( DBManip,
                    'The associated mailbox could not been retrieved, the database may be corrupted' ) )

            # Is the password OK ?
            elif not check_dovecot_passwd ( associated_mailbox['address'],
                request.form.get( 'old_password' ) ) :
                errors.append( Error( WrongArg,
                    'Wrong password' ) )

             
            else:
                # If there is an end_date or there was but not anymore
                if request.form.get('end') or (not request.form.get('end') and alias['end_date']):
                    try :
                        # Get the date limit if there is one
                        end_date=None
                        if request.form.get('end') :
                            end_str = "-".join([request.form.get(select).zfill(2) for select in ['endyear', 'endmonth', 'endday', 'endhour', 'endmin', 'endsec']])
                            end_date=datetime.strptime(end_str, "%Y-%m-%d-%H-%M-%S")
                        
                        # Update the database
                        db.execute('UPDATE mails SET end_date=? WHERE id=?', [end_date, alias_id])
                        db.commit()
                    except sqlite3.OperationalError :
                        # Exceptions about database
                        errors.append( Error( DBManip,
                            'Something went wrong while updating the database' ) )
                        log (sys.exc_info(), level='ERROR')
                    except ValueError :
                        # Exceptions about datetime wrong value
                        errors.append( Error( Hacker,
                            'Please don\'t even try to mess up with the form' ) )
                        log (sys.exc_info(), 'Error')
                    except :
                        # Other exceptions
                        errors.append( Error( Unknown,
                            'Something went wrong' ) )
                        log (sys.exc_info(), 'Error')
                        raise
                    else :
                        # Everyting is ok and notify the user about success
                        if request.form.get('end') :
                            log ('Set alias '+alias['address']+' end limit to '+end_date.isoformat())
                            flash ('End limit for '+alias['address']+' changed to '+end_date.isoformat())
                        else :
                            log ('Removed end limit for alias '+alias['address'])
                            flash ('Removed end limit for '+alias['address'])
        
    # Reload data from database in case of a change
    cur = db.execute('SELECT address, end_date FROM mails WHERE id=?', [alias_id])
    alias = cur.fetchone()
    return render_template( 'editalias.html', alias=alias['address'], end_date=alias['end_date'], errors=errors)

                 
@app.route('/editmailbox/<int:mailbox_id>', methods=['GET', 'POST'])
def edit_mailbox(mailbox_id) :
    """The web page to edit a mailbox informations"""

    if not session.get('user_id') :
        return redirect( url_for( 'login', redir='mails' ) )

    # Get some info about the mailbox asked to be edited
    db = get_db()
    cur = db.execute('SELECT address, target_id, end_date FROM mails WHERE id=?', [mailbox_id])
    mailbox = cur.fetchone()

    # Does the mailbox exists or is it an alias ?
    if not mailbox or mailbox['target_id']:
        flash( 'The alias asked to be deleted doesn\'t exists or is not a mailbox' )
        return redirect( url_for( 'mails' ) )

    # Possible errors
    errors = []

    # Has the user filled in the form ?
    if request.method == 'POST' :
        # Is the old_password field not empty
        if not request.form.get( 'old_password' ) :
            errors.append( Error( ConfPasswd,
                "You must fill in the password field to be able to modify anything" ) )

        # Is the password OK ?
        elif not check_dovecot_passwd ( mailbox['address'], request.form.get( 'old_password' ) ) :
            errors.append( Error( WrongArg,
                'Wrong password' ) )

         
        else:
            # If the user tryed to change the password
            if request.form.get('new_password1') or request.form.get('new_password2') :
                # If only one password field is filled :
                if not request.form.get('new_password1') or not request.form.get('new_password2') :
                    errors.append( Error( MissingArg,
                        'Both password field must be filled in order to change the password' ) )
                # If password are not the same
                elif request.form.get('new_password1') != request.form.get('new_password2') :
                    errors.append( Error( WrongArg,
                        'Both password don\'t match' ) )
                # Change the password, log and notify the user of success
                elif not change_dovecot_passwd( mailbox['address'], request.form.get( 'new_password1') ) :
                    errors.append( Error( DovecotManip,
                        'Something went wrong while changing the password. Check the logs for more details' ) )
                else :
                    log( 'Password for the mailbox '+mailbox['address']+' changed' )
                    flash( 'The password for '+mailbox['address']+' has been successfully changed' )


            # If there is an end_date or there was but not anymore
            if request.form.get('end') or ( not request.form.get('end') and mailbox['end_date'] ) :
                try :
                    # Get the date limit if there is one
                    end_date=None
                    if request.form.get('end') :
                        end_str = "-".join(
                                [ request.form.get(select).zfill(2) for select in 
                                    ['endyear', 'endmonth', 'endday',
                                     'endhour', 'endmin', 'endsec']
                                ]
                            )
                        end_date=datetime.strptime(end_str, "%Y-%m-%d-%H-%M-%S")
                    
                    # Update the database
                    db.execute('UPDATE mails SET end_date=? WHERE id=?',
                            [end_date, mailbox_id])
                    db.commit()
                except sqlite3.OperationalError :
                    # Exceptions about database
                    errors.append( Error( DBManip,
                        'Something went wrong while updating the database' ) )
                    log (sys.exc_info(), 'Error')
                except ValueError :
                    # Exceptions about datetime wrong value
                    errors.append( Error( Hacker,
                        'Please don\'t even try to mess up with the form' ) )
                    log (sys.exc_info(), 'Error')
                except :
                    # Other exceptions
                    errors.append( Error( Unknown,
                        'Something went wrong' ) )
                    log (sys.exc_info(), 'Error')
                    raise
                else :
                    # Everyting is ok and notify the user about success
                    if request.form.get('end') :
                        log ('Set mailbox '+mailbox['address']+' end limit to '+end_date.isoformat())
                        flash ('End limit for '+mailbox['address']+' changed to '+end_date.isoformat())
                    else :
                        log ('Removed end limit for mailbox '+mailbox['address'])
                        flash ('Removed end limit for '+mailbox['address'])
        
    # Reload data from database in case of a change
    cur = db.execute('SELECT address, end_date FROM mails WHERE id=?', [mailbox_id])
    mailbox = cur.fetchone()
    return render_template( 'editmailbox.html', mailbox=mailbox['address'], end_date=mailbox['end_date'], errors=errors)



@app.route('/delmail/<int:mail_id>', methods=['GET', 'POST'])
def del_mail(mail_id) :
    """The web page to delete a mail (either alias or mailbox)"""

    if not session.get('user_id') :
        return redirect( url_for( 'login', redir='mails' ) )

    # Get some info about the mail asked to be deleted
    db = get_db()
    cur = db.execute('SELECT address, target_id FROM mails WHERE id=?', [mail_id])
    mail = cur.fetchone()

    # Does the mail exists
    if not mail :
        flash ('The mail asked to be deleted doesn\'t exists')
        return redirect( url_for( 'mails' ) )

    # Possible errors
    errors = []

    # Has the user filled in the form ?
    if request.method == 'POST' :

        # Is the password field not empty ?
        if not request.form.get( 'password' ) :
            errors.append( Error( MissingArg,
                'Please fill the password field' ) )
        else :

            # Does the mail have a target_id (= alias )
            if mail['target_id'] :

                # Get info about the associated mailbox
                cur = db.execute( 'SELECT address FROM mails WHERE id=?', [mail['target_id']])
                associated_mailbox = cur.fetchone()
                
                # Is the password correct ?
                if not check_dovecot_passwd( associated_mailbox['address'],
                        request.form.get( 'password' ) ) :
                    errors.append( Error( WrongArg,
                        'Wrong password' ) )
                # You can delete the mail
                else :
                    del_alias( mail_id )
                    if not update_postfix_mails() :
                        errors.append( Error( PostfixManip,
                            'Something went wrong while updating postfix. Check the logs for more details.' ) )
                    return redirect( url_for( 'mails' ) )

            # If it's a mailbox
            else :

                # Is the password correct ?
                if not check_dovecot_passwd( mail['address'],
                        request.form.get( 'password' ) ) :
                    errors.append( Error( WrongArg,
                        'Wrong password' ) )
                # You can delete the mail
                else :
                    del_mailbox( mail_id )
                    if not update_postfix_mails() :
                        errors.append( Error( PostfixManip,
                            'Something went wrong while updating postfix. Check the logs for more details.' ) )
                    return redirect( url_for( 'mails' ) )

    # Render the HTML template with associated error if necessary
    return render_template('delmail.html', mail=mail['address'], errors=errors)


def del_alias(alias_id) :
    """Delete a specific alias. Not assiociated with an URL so assume the alias_id
    exists and is trully and alias. This verification must have been done earlier."""
    
    db = get_db()
    try :
        db.execute('DELETE FROM mails WHERE id=?', [alias_id])
        db.commit()
    except :
        log (sys.exc_info(), 'Error')
        flash ('Something went wrong while deleting the alias from the database')
    else :
        flash ('Alias successfully deleted')


def del_mailbox(mailbox_id) :
    """Delete a specific mailbox. Not associated with an URL so assume the mailbox_id
    has been verified earlier as a correct one."""

    db = get_db()
    try :
        db.execute('DELETE FROM mails WHERE target_id=?', [mailbox_id])
        db.execute('DELETE FROM mails WHERE id=?', [mailbox_id])
        db.commit()
    except :
        log (sys.exc_info(), 'Error')
        flash ('Something went wrong while deleting the mailbox from the database')
    else :
        flash ('Mailbox successfully deleted')





@app.route('/filters/', methods=['GET'])
def filters():
    """The filter web page"""

    if not session.get('user_id') :
        return redirect( url_for( 'login', redir='filters' ) )

    # Get all possible mailbox
    db = get_db()
    cur = db.execute( 'SELECT id, address FROM mails WHERE target_id ISNULL' )
    mailboxes = cur.fetchall()

    return render_template('filters.html', mailboxes=mailboxes)




@app.route('/editfilter/<int:mailbox_id>', methods=['GET', 'POST'])
def edit_filter( mailbox_id ) :

    if not session.get('user_id') :
        return redirect( url_for( 'login', redir='filters' ) )

    # Check if this mailbox is in the database
    db = get_db()
    cur = db.execute( 'SELECT address, target_id FROM mails WHERE id=?', [mailbox_id] )
    mailbox = cur.fetchone()

    if not mailbox :
        flash( 'The filter you\'ve asked for is not associated with a mailbox' )
        return redirect( url_for( 'filters' ) )

    # Possible errors
    errors = []

    # If the user entered a new content
    if request.method == 'POST' :
        # Is the given password correct ?
        if not request.form.get('password') :
            errors.append( Error( MissingArg,
                "No password given" ) )
        elif not check_dovecot_passwd( mailbox['address'],
                request.form.get('password') ) :
            errors.append( Error( WrongArg,
                "Wrong password" ) )
        else :
            # Get the new content
            new_content = request.form.get('new_content')

            # Is the content correctly written ?
            check = check_sieve_filter_content( new_content )
            if check[0] :
                if not set_sieve_filter_content( mailbox['address'], new_content ) :
                    errors.append( Error( SieveManip,
                        'Something went wrong while writing the new sieve file. Check the logs for more details.' ) )
                else :
                    flash( 'New sieve file sucessfully written' )
                    return redirect( url_for( 'filters' ) )
            else :
                errors.append( Error( SieveSyntax,
                    check[1] ) )
        


    content = get_sieve_filter_content( mailbox['address'] )

    return render_template( 'editfilter.html', mailbox=mailbox, content=content, errors=errors )


    


@app.route('/edituser', methods=['GET', 'POST'])
def edit_user():
    """The page where a user can edit it's personal infos"""

    user_id = session.get('user_id')
    if not user_id :
        return redirect( url_for( 'login', redir='edit_user' ) )

    # Possible errors
    errors = []

    # Get the actual informations stored
    db = get_db()
    cur = db.execute('SELECT id, username, password, salt FROM users WHERE id=?', [user_id])
    user = cur.fetchone()

    # Does the user exists or did sth went wrong ?
    # We force logout to be sure it's not an old session
    if not user:
        flash('Something went wrong : it seems your account doesn\'t exists anymore')
        return logout()

    # The POST method is used (= the user has filled the form with new infos)
    if request.method == 'POST':
        # Is the confirmation password correct :
        if not request.form.get('old_password') :
            errors.append( Error( MissingArg,
                "No password given" ) )
        elif not saltpassword(request.form.get('old_password'), user['salt']) == user['password'] :
            errors.append( Error( WrongArg,
                "Wrong password" ) )
        else :
            # Has the username been changed ?
            if request.form.get('username') and request.form.get('username') != user['username']:
                username = request.form.get('username')
                # Trying to change the name in the database
                try :
                    db.execute('UPDATE users SET username=? WHERE id=?',
                            [username, user_id])
                    db.commit()
                except :
                    errors.append( Error( DBManip,
                        'Something went wrong while modifying your username' ) )
                    log (sys.exc_info(), 'Error')
                else:
                    log('Username changed from '+user['username']+' to '+username)
                    flash ('Your username has successfully been changed to '+username)


            # Has the password been changed ?
            if request.form.get('new_password1') or request.form.get('new_password2') :
                if not request.form.get('new_password1') or not request.form.get('new_password2') :
                    # One of the two password field is empty
                    errors.append( Error( MissingArg,
                        'Please fill in both password field' ) )
                elif request.form.get('new_password1') != request.form.get('new_password2') :
                    # Both password field don't match
                    errors.append( Error( WrongArg,
                        'Passwords don\'t match' ) )
                else :
                    # Everything is allright let's get password and salt ready
                    password = request.form.get('new_password1')
                    salt = randint(1000000, 1000000000)
                    # Trying to actually modify the db
                    try :
                        db.execute('UPDATE users SET password=?, salt=? WHERE id=?',
                                [saltpassword(password, salt), salt, user_id])
                        db.commit()
                    except :
                        errors.append( Error( DBManip,
                            'Something went wrong while changing your password' ) )
                        log (sys.exc_info(), 'Error')
                    else :
                        log(user['username']+'s password modified')
                        flash('Your password has been successfully modified')

    # In case something has changed we reload data from the db
    # So we're sure to be up to date
    user = db.execute('SELECT id, username FROM users WHERE id=?', [user_id]).fetchone()

    # Back to the edituser page but with error or success displayed
    return render_template('edituser.html', user=user, errors=errors)




@app.route( '/login/<redir>', methods=['GET', 'POST'])
def login( redir ):
    """The login page (standard username + passwd connection)"""

    # Possible errors
    errors = []

    # Has the user used POST method (= try to login )
    if request.method == 'POST':
        # Are all fields filled ?
        if request.form.get('username') and request.form.get('password') :
            # Get infos from database
            db = get_db()
            cur = db.execute('SELECT id, username, password, salt FROM users WHERE username=?',
                    [request.form.get('username')])
            user = cur.fetchone()

            # Does this user exists
            if not user :
                errors.append( Error( WrongArg,
                    'Incorrect credentials' ) )
            else :
                # Is the given password the correct one
                if saltpassword(request.form.get('password'), user['salt']) == user['password'] :
                    session['user_id'] = user['id']
                    log('User '+request.form.get('username')+' connected')
                    flash('Successfully connected')

                    # Try to go back to the redir page
                    try :
                        ret = redirect( url_for( redir ) )
                        return ret
                    except :
                        flash( 'A wrong URL was given so you\'ve been redirected to the welcome page' )
                        log (sys.exc_info(), 'Error')
                        return redirect( url_for( 'welcome' ) )

                else :
                    errors.append( Error( WrongArg,
                        'Incorrect credentials' ) )
        else :
            errors.append( Error( MissingArg,
                'No credentials given' ) )

    # In case of failed connection or GET method (= display page )
    return render_template('login.html', errors=errors)


@app.route('/logout')
def logout():
    # The user id
    user_id = session.get('user_id')
    if not user_id :
        flash( 'You were already logged out' )
    else :
        db = get_db()
        cur = db.execute( 'SELECT username FROM users WHERE id = ?', [user_id] )
        user = cur.fetchone()
        
        if not user :
            flash( 'It seems your session was linked to an unexisting account' )
            log( 'Logout of unexisting account : '+str(user_id), level='ERROR')
        else :
            session.pop('user_id', None)
            log( 'User '+user['username']+' disconnected' )
            flash('You succesfully logged out')

    return redirect( url_for( 'welcome' ) )
