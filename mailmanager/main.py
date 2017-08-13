# -*- coding: utf-8 -*-

# all the imports
import os
import sqlite3
import time
from hashlib import sha256
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

    if not session.get('logged_in') :
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





@app.route('/addalias/<int:id>', methods=['GET', 'POST'])
def add_alias(id):
    return welcome()

@app.route('/addmailbox', methods=['GET', 'POST'])
def add_mailbox():
    return welcome()





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
            cur = db.execute('SELECT username, password, salt FROM users WHERE username=?',
                    [request.form['username']])
            user = cur.fetchone()

            # Does this user exists
            if not user :
                error = 'Incorrect credentials'
            else :
                # Is the given password the correct one
                if saltpassword(request.form['password'], user['salt']) == user['password'] :
                    session['logged_in'] = True
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
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('login'))
