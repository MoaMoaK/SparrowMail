# -*- coding: utf-8 -*-

# Import PyPI packages
import os
import sqlite3
import time
from random import randint
from hashlib import sha256

# Import other packages
from email_validator import validate_email, EmailNotValidError

# Import flask packages
from flask import Flask, request, session, g, redirect, url_for, abort, \
             render_template, flash

app = Flask(__name__) # create the application instance :)
app.config.from_object(__name__) # load config from this file , mailmanager.py

#Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'mailmanager.db'),
    SECRET_KEY='development-key',
    ))
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
    with app.open_resource('schema.sql', mode='r') as f:
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

    print(time.ctime() + ' ['+level+'] ' + message)
    return None



@app.route('/', methods=['GET'])
def welcome():
    """The default web page presenting the different mail infos"""

    if not session.get('user_id') :
        return redirect( url_for( 'login' ) )
    else :
        # Get the mailboxes and aliases from database (mails = mailboxes + aliases)
        mails = []

        db = get_db()

        cur = db.execute('SELECT id, address FROM mailboxes')
        mailboxes = cur.fetchall()

        for mailbox in mailboxes :
            cur = db.execute('SELECT id, address FROM aliases WHERE target_id=?',
                    [mailbox['id']])
            aliases = cur.fetchall()

            mails.append ({'address': mailbox['address'],
                            'id': mailbox['id'],
                            'aliases' : aliases})

        return render_template('welcome.html', mails=mails)





@app.route('/addalias/<int:mailbox_id>', methods=['GET', 'POST'])
def add_alias(mailbox_id):
    """The page to add 1 alias to a specific mailbox"""
    
    if not session.get('user_id') :
        return redirect(url_for('login'))

    # Get the address associated with the wanted id
    db = get_db()
    cur = db.execute('SELECT address FROM mailboxes WHERE id=?', [mailbox_id])
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
        if not request.form['alias'] :
            error = 'The alias field can\'t be empty'
        else :
            try :
                # Is it a valid email ?
                v = validate_email(request.form['alias'])
                alias = v['email']
                # If no exceptions so far, let's update the db
                db.execute('INSERT INTO aliases (address, target_id) VALUES (?, ?)',
                        [alias, mailbox_id])
                db.commit()
            except EmailNotValidError as e :
                # Only exception from validate_email (= email not valid )
                error = request.form['alias']+' is not a valid email'
                log (sys.exc_info())
            except :
                # Other exceptions ( about database request )
                error = 'Something went wrong while updating the database'
                log (sys.exc_info())
            else :
                # Everyting is ok, notify the user about success and go back to welcome page
                log ('Alias '+alias+' added to '+str(mailbox_id))
                flash (alias+' has been successfully added as an alias')
                return redirect(url_for('welcome'))

    # In case of something wrong, go back to the form with the error displayed
    return render_template('addalias.html', error=error, mailbox_address=mailbox['address'])




@app.route('/addmailbox', methods=['GET', 'POST'])
def add_mailbox():
    return welcome()




@app.route('/edituser/', methods=['GET', 'POST'])
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
        if request.form['username'] and request.form['username'] != user['username']:
            username = request.form['username']
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
        if request.form['password1'] or request.form['password2'] :
            if not request.form['password1'] or not request.form['password2'] :
                # One of the two password field is empty
                error_pass = 'Please fill in both password field'
            elif request.form['password1'] != request.form['password2'] :
                # Both password field don't match
                error_pass = 'Password don\'t match'
            else :
                # Everything is allright let's get password and salt ready
                password = request.form['password1']
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
        if request.form['username'] and request.form['password'] :
            # Get infos from database
            db = get_db()
            cur = db.execute('SELECT id, username, password, salt FROM users WHERE username=?',
                    [request.form['username']])
            user = cur.fetchone()

            # Does this user exists
            if not user :
                error = 'Incorrect credentials'
            else :
                # Is the given password the correct one
                if saltpassword(request.form['password'], user['salt']) == user['password'] :
                    session['user_id'] = user['id']
                    log('User '+request.form['username']+' connected')
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
