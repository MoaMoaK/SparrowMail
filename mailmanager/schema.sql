DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id integer primary key autoincrement,
    username text not null unique,
    password text not null,
    salt text net null
);

DROP TABLE IF EXISTS mailboxes;
CREATE TABLE mailboxes (
    id integer primary key autoincrement,
    address text not null unique
);

DROP TABLE IF EXISTS aliases;
CREATE TABLE aliases (
    id integer primary key autoincrement,
    address text not null unique,
    target_id integer
);

