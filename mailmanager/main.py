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
from mailmanager.scripts import postfix
from mailmanager.scripts import dovecot

app = Flask(__name__) # create the application instance :)
app.config.from_object('mailmanager.config') # load config from the config.py file

# Override config from an environment variable
app.config.from_envvar('MAILMANAGER_SETTINGS', silent=True)

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
    """Initializes the database."""
    init_db()
    log('Initialized the database.')




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

    postfix.update(app.config['ALIASES_FILE_PATH'], app.config['MAILBOXES_FILE_PATH'],
            aliases_list, mailboxes_list)

def add_dovecot_passwd( mailbox_add, pw ) :
    """Triggers the dovecot.update_passwd function with the right info"""
    
    dovecot.add_passwd(app.config['PASSWD_FILE_PATH'], mailbox_add, pw)

def check_dovecot_passwd( mailbox_add, pw ):
    """Triggers the dovecot.check_passwd function with the right info"""

    return dovecot.check_passwd(app.config['PASSWD_FILE_PATH'], mailbox_add, pw)





@app.route('/', methods=['GET'])
def welcome():
    """The default welcome web page"""

    return render_template('welcome.html')

@app.route('/folders/', methods=['GET'])
def folders():
    """The folder web page"""

    return render_template('folders.html')
    
@app.route('/filters/', methods=['GET'])
def filters():
    """The filter web"""

    return render_template('filters.html')

@app.route('/mails/', methods=['GET'])
def mails():
    """The web page presenting the different mail infos"""

    if not session.get('user_id') :
        return redirect( url_for( 'login' ) )

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
        return redirect(url_for('login'))

    # Get the address associated with the wanted id
    db = get_db()
    cur = db.execute('SELECT address FROM mails WHERE id=? AND target_id ISNULL', [mailbox_id])
    mailbox = cur.fetchone()

    # Is the mailbox_id valid ?
    if not mailbox :
        flash ('The mailbox you\'ve asked to add an alias to doesn\'t exist')
        return redirect(url_for('welcome'))
    
    # Possible error
    error = None

    # Has the user filled the form ?
    if request.method == 'POST' :
        # Is the field not empty
        if not request.form.get('alias') :
            error = 'The alias field can\'t be empty'
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
                update_postfix_mails()

            except EmailNotValidError :
                # Only exception from validate_email (= email not valid )
                error = request.form.get('alias')+' is not a valid email'
                log (sys.exc_info())
            except sqlite3.OperationalError :
                # Exceptions about database request
                error = 'Something went wrong while updating the database'
                log (sys.exc_info())
            except sqlite3.IntegrityError :
                # Exceptions about integrity of database probably unique constraint
                error = 'This mail address may be used, try another one'
                log (sys.exc_info())
            except ValueError :
                # Exceptions about datetime wrong value
                erro = 'Please don\'t even try to mess up with the form'
                log (sys.exc_info())
            except :
                # Other excpetions
                error = 'Something went wrong'
                log (sys.exc_info())
            else :
                # Everyting is ok, notify the user about success and go back to welcome page
                log ('Alias '+new_alias+' added to '+mailbox['address'])
                flash (new_alias+' has been successfully added as an alias')
                return redirect(url_for('mails'))

    # If GET method used or
    # In case of something wrong, go back to the form with the error displayed
    return render_template('addalias.html', error=error, mailbox_address=mailbox['address'])




@app.route('/addmailbox', methods=['GET', 'POST'])
def add_mailbox():
    """The page to add 1 mailbox"""
    
    if not session.get('user_id') :
        return redirect(url_for('login'))

    # Possible error
    error = None

    # Has the user filled the form ?
    if request.method == 'POST' :
        # Is the mailbox field not empty
        if not request.form.get('mailbox') :
            error = 'The mailbox field can\'t be empty'
        # Are the password fields not empty
        elif not request.form.get('password1') or not request.form.get('password2'):
            error = 'Please fill in the password field'
        elif request.form.get('password1') != request.form.get('password2'):
            error = 'Password don\'t match'
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
                update_postfix_mails()

                # Update the password file
                add_dovecot_passwd(new_mailbox, request.form.get('password1'))

            except EmailNotValidError :
                # Only exception from validate_email (= email not valid )
                error = request.form.get('mailbox')+' is not a valid email'
                log (sys.exc_info())
            except sqlite3.OperationalError :
                # Exceptions about database
                error = 'Something went wrong while updating the database'
                log (sys.exc_info())
            except sqlite3.IntegrityError :
                # Exceptions about integrity of database probably unique constraint
                error = 'This mail address may be used, try another one'
                log (sys.exc_info())
            except ValueError :
                # Exceptions about datetime wrong value
                error = 'Please don\'t even try to mess up with the form'
                log (sys.exc_info())
            except :
                # Other exceptions
                error = 'Something went wrong'
                log (sys.exc_info())
                raise
            else :
                # Everyting is ok, notify the user about success and go back to mails page
                log ('Mailbox '+new_mailbox+' added')
                flash (new_mailbox+' has been successfully added as a mailbox')
                return redirect(url_for('mails'))
    
    # If GET method used or
    # In case of something wrong, go back to the form with the error displayed
    return render_template('addmailbox.html', error=error)



@app.route('/delmail/<int:mail_id>', methods=['GET', 'POST'])
def del_mail(mail_id) :
    """The web page to delete a mail (either alias or mailbox)"""

    if not session.get('user_id') :
        return redirect(url_for('login'))

    # Get some info about the mail asked to be deleted
    db = get_db()
    cur = db.execute('SELECT address, target_id FROM mails WHERE id=?', [mail_id])
    mail = cur.fetchone()

    # Does the mail exists
    if not mail :
        flash ('The mail asked to be deleted doesn\'t exists')
        return redirect( url_for( 'mails' ) )

    # Possible error
    error = None

    # Has the user filled in the form ?
    if request.method == 'POST' :

        # Is the password field not empty ?
        if not request.form.get( 'password' ) :
            error = 'Please fill the password field'

        else :

            # Does the mail have a target_id (= alias )
            if mail['target_id'] :

                # Get info about the associated mailbox
                cur = db.execute( 'SELECT address FROM mails WHERE id=?', mail['target_id'])
                associated_mailbox = cur.fetchone()
                
                # Is the password correct ?
                if not check_dovecot_passwd( associated_mailbox['address'],
                        request.form.get( 'password' ) ) :
                    error = 'Wrong password'
                # You can delete the mail
                else :
                    del_alias( mail_id )

            # If it's a mailbox
            else :

                # Is the password correct ?
                if not check_dovecot_passwd( mail['address'],
                        request.form.get( 'password' ) ) :
                    error = 'Wrong password'
                # You can delete the mail
                else :
                    del_mailbox( mail_id )

            update_postfix_mails()
            return redirect( url_for( 'mails' ) )

    # Render the HTML template with associated error if necessary
    return render_template('delmail.html', error=error)


def del_alias(alias_id) :
    """Delete a specific alias. Not assiociated with an URL so assume the alias_id
    exists and is trully and alias. This verification must have been done earlier."""
    
    db = get_db()
    try :
        db.execute('DELETE FROM mails WHERE id=?', [alias_id])
        db.commit()
    except :
        log (sys.exc_info())
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
        log (sys.exc_info())
        flash ('Something went wrong while deleting the mailbox from the database')
    else :
        flash ('Mailbox successfully deleted')

    


@app.route('/edituser', methods=['GET', 'POST'])
def edit_user():
    """The page where a user can edit it's personal infos"""

    user_id = session.get('user_id')
    if not user_id :
        return redirect(url_for('login'))

    # Errors about the name or the password
    error_name = None
    error_pass = None

    # Get the actual informations stored
    db = get_db()
    cur = db.execute('SELECT id, username FROM users WHERE id=?', [user_id])
    user = cur.fetchone()

    # Does the user exists or did sth went wrong ?
    # We force logout to be sure it's not an old session
    if not user:
        flash('Something went wrong : it seems your account doesn\'t exists anymore')
        return logout()

    # The POST method is used (= the user has filled the form with new infos)
    if request.method == 'POST':
        # Has the username been changed ?
        if request.form.get('username') and request.form.get('username') != user['username']:
            username = request.form.get('username')
            # Trying to change the name in the database
            try :
                db.execute('UPDATE users SET username=? WHERE id=?',
                        [username, user_id])
                db.commit()
            except :
                error_name = 'Something went wrong while modifying your username'
                log(sys.exc_info())
            else:
                log('Username changed from '+user['username']+' to '+username)
                flash ('Your username has successfully been changed to '+username)


        # Has the password been changed ?
        if request.form.get('password1') or request.form.get('password2') :
            if not request.form.get('password1') or not request.form.get('password2') :
                # One of the two password field is empty
                error_pass = 'Please fill in both password field'
            elif request.form.get('password1') != request.form.get('password2') :
                # Both password field don't match
                error_pass = 'Password don\'t match'
            else :
                # Everything is allright let's get password and salt ready
                password = request.form.get('password1')
                salt = randint(1000000, 1000000000)
                # Trying to actually modify the db
                try :
                    db.execute('UPDATE users SET password=?, salt=? WHERE id=?',
                            [saltpassword(password, salt), salt, user_id])
                    db.commit()
                except :
                    error_pass = 'Something went wrong while changing your password'
                    log(sys.exc_info())
                else :
                    log(user['username']+'s password modified')
                    flash('Your password has been successfully modified')

    # In case something has changed we reload data from the db
    # So we're sure to be up to date
    user = db.execute('SELECT id, username FROM users WHERE id=?', [user_id]).fetchone()

    # Back to the edituser page but with error or success displayed
    return render_template('edituser.html', user=user, error_name=error_name, error_pass=error_pass)





@app.route('/login/', methods=['GET', 'POST'])
def login():
    """The login page (standard username + passwd connection)"""

    error = None

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
                error = 'Incorrect credentials'
            else :
                # Is the given password the correct one
                if saltpassword(request.form.get('password'), user['salt']) == user['password'] :
                    session['user_id'] = user['id']
                    log('User '+request.form.get('username')+' connected')
                    flash('Successfully connected')
                    # back to the welcome page

                    return redirect(url_for('welcome'))
                else :
                    error = 'Incorrect credentials'
        else :
            error = 'No credentials given'

    # In case of failed connection or GET method (= display page )
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You were logged out')
    return redirect(url_for('login'))
