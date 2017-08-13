DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id integer primary key autoincrement,
    username text not null unique,
    password text not null,
    salt text net null
);

INSERT INTO users (username, password, salt)
VALUES ("moamoak", "eda1b367003c6dd6a3e5650a2bd02b393947e37d3f7184b736802ce7afe5c7c8", "123456789");
