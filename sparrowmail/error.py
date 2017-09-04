# -*- coding: utf-8 -*-

class ErrorCategory :
    def __init__( self, name ) :
        self.name = name

    def getName( self ) :
        return self.name

MissingArg   = ErrorCategory( 'Missing argument'          )
WrongArg     = ErrorCategory( 'Wrong argument'            )
DBManip      = ErrorCategory( 'Database manipulation'     )
SieveManip   = ErrorCategory( 'Sieve file manipulation'   )
SieveSyntax  = ErrorCategory( 'Sieve syntax'              )
DovecotManip = ErrorCategory( 'Dovecot file manipulation' )
PostfixManip = ErrorCategory( 'Postfix file manipulation' )
Hacker       = ErrorCategory( 'R U H4ck3r ?'              )
Unknown      = ErrorCategory( ''                          )
ConfPasswd   = ErrorCategory( 'Confirmation password'     )

class Error :
    def __init__( self, cat, info ) :
        self.cat = cat
        self.info = info

    def getCategory( self ) :
        return self.cat

    def getInfo( self ) :
        return self.info

    def message( self ) :
        catName = self.getCategory().getName()
        if catName == '' :
            return '<strong>Error :</strong> '+self.getInfo()
        else :
            return '<strong> Error ('+self.getCategory().getName()+') :</strong> '+self.getInfo().replace('\n', '<br>')
