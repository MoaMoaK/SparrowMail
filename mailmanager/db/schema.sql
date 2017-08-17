DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id integer primary key autoincrement,
    username text not null unique,
    password text not null,
    salt text net null
);

DROP TABLE IF EXISTS mails;
CREATE TABLE mails (
    id           integer primary key autoincrement,
    address      text    not null unique,
    target_id    integer,
    end_date     integer
);
