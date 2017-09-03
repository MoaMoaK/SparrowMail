DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id integer primary key autoincrement,
    username text not null unique,
    password text not null,
    salt text not null
);

INSERT INTO users (username, password, salt)
VALUES ("user", "b2d1349ea3f52597f37566ed4095e10729c8329c612b64563849dcf29ee9de6e", "123456789");

DROP TABLE IF EXISTS mails;
CREATE TABLE mails (
    id           integer primary key autoincrement,
    address      text    not null unique,
    target_id    integer,
    end_date     integer
);
