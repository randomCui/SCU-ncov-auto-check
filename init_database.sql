create table save_history
(
    stu_id    TEXT,
    post_time REAL,
    save_info TEXT,
    result    TEXT,
    cookie    TEXT,
    status    INTEGER
);

create table user
(
    stu_id      TEXT,
    enable      TEXT,
    create_time INTEGER,
    password    TEXT,
    cookie      TEXT
);