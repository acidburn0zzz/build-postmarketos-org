CREATE TABLE db_version
(
    version INT NOT NULL
);

INSERT INTO `db_version`
VALUES (0);

CREATE TABLE package
(
    aport VARCHAR(100) NOT NULL,
    arch VARCHAR(10) NOT NULL,
    component VARCHAR(30) NOT NULL,
    time_spent BIGINT DEFAULT NULL,
    times_built INT DEFAULT NULL
);

CREATE TABLE log
(
    datetime DATETIME NOT NULL,
    action VARCHAR(100) NOT NULL,
    details LONGTEXT DEFAULT NULL,
    payload LONGTEXT DEFAULT NULL
);

UPDATE `db_version` SET `version` = 1;
