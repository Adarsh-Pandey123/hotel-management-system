-- ============================================================
-- Hotel Management System - database schema and sample data
-- Run with:  mysql -u root -p < database/hotel.sql
-- Safe to run more than once (it never drops existing data).
-- ============================================================

CREATE DATABASE IF NOT EXISTS hotel;
USE hotel;

-- Hotel details and tax rates (read by the application at start-up)
CREATE TABLE IF NOT EXISTS setting (
    id          INT          NOT NULL AUTO_INCREMENT,
    field_name  VARCHAR(30)  NOT NULL,
    value       VARCHAR(100),
    PRIMARY KEY (id),
    UNIQUE KEY uq_setting_field (field_name)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS rooms (
    id          INT           NOT NULL AUTO_INCREMENT,
    room_no     INT           NOT NULL,
    room_type   VARCHAR(30),
    room_rent   DECIMAL(10,2),
    room_bed    VARCHAR(20),
    status      VARCHAR(20)   NOT NULL DEFAULT 'free',   -- free / occupied / renovation
    PRIMARY KEY (id),
    UNIQUE KEY uq_rooms_room_no (room_no)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS customer (
    id           BIGINT       NOT NULL AUTO_INCREMENT,
    name         VARCHAR(50),
    address      VARCHAR(100),
    phone        VARCHAR(15),
    email        VARCHAR(80),
    id_proof     VARCHAR(20),
    id_proof_no  VARCHAR(25),
    males        INT          DEFAULT 0,
    females      INT          DEFAULT 0,
    children     INT          DEFAULT 0,
    PRIMARY KEY (id)
) ENGINE=InnoDB;

-- doo = date of occupancy (check-in), dol = date of leaving (check-out, NULL while staying)
CREATE TABLE IF NOT EXISTS booking (
    book_id   BIGINT        NOT NULL AUTO_INCREMENT,
    room_id   INT           NOT NULL,
    cust_id   BIGINT        NOT NULL,
    doo       DATE          NOT NULL,
    dol       DATE          NULL,
    advance   DECIMAL(10,2) NOT NULL DEFAULT 0,
    PRIMARY KEY (book_id),
    CONSTRAINT fk_booking_room FOREIGN KEY (room_id) REFERENCES rooms (id),
    CONSTRAINT fk_booking_customer FOREIGN KEY (cust_id) REFERENCES customer (id)
) ENGINE=InnoDB;

-- gst / st store the tax percentages that were applied to this bill
CREATE TABLE IF NOT EXISTS bill (
    bill_id    BIGINT        NOT NULL AUTO_INCREMENT,
    book_id    BIGINT        NOT NULL,
    amount     DECIMAL(10,2),
    bill_date  DATE,
    gst        DECIMAL(5,2),
    st         DECIMAL(5,2),
    PRIMARY KEY (bill_id),
    UNIQUE KEY uq_bill_booking (book_id),
    CONSTRAINT fk_bill_booking FOREIGN KEY (book_id) REFERENCES booking (book_id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Sample data (fictional - change it from the Settings menu)
-- ------------------------------------------------------------
INSERT IGNORE INTO setting (id, field_name, value) VALUES
    (1, 'hotel_name', 'Hotel Sample'),
    (2, 'address',    '123 Main Street, Your City'),
    (3, 'phone',      '9999999999'),
    (4, 'email',      'info@example.com'),
    (5, 'gst',        '12'),
    (6, 'st',         '5');

INSERT IGNORE INTO rooms (id, room_no, room_type, room_rent, room_bed, status) VALUES
    (1,  1,  'AC',                 2500.00, 'SINGLE', 'free'),
    (2,  2,  'AC',                 2500.00, 'SINGLE', 'free'),
    (3,  3,  'AC',                 3500.00, 'DOUBLE', 'free'),
    (4,  4,  'DELUX',              4500.00, 'DOUBLE', 'free'),
    (5,  5,  'DELUX',              4500.00, 'DOUBLE', 'free'),
    (6,  6,  'SUPER DELUX',        5500.00, 'DOUBLE', 'free'),
    (7,  7,  'QUEEN DELIGHT',      6500.00, 'DOUBLE', 'free'),
    (8,  8,  'KINGS SPECIAL',      7500.00, 'DOUBLE', 'free'),
    (9,  9,  'SUPER RICH SPECIAL', 9500.00, 'TRIPLE', 'free'),
    (10, 10, 'AC',                 3000.00, 'TRIPLE', 'free');

INSERT IGNORE INTO customer
    (id, name, address, phone, email, id_proof, id_proof_no, males, females, children) VALUES
    (1, 'Rahul Sharma', '12 GANDHI NAGAR, DELHI',  '9000000001', 'RAHUL@EXAMPLE.COM', 'AADHAR',   'XXXX-XXXX-0001', 1, 1, 2),
    (2, 'Priya Verma',  '45 CIVIL LINES, LUCKNOW', '9000000002', 'PRIYA@EXAMPLE.COM', 'PASSPORT', 'P0000002',      0, 1, 0),
    (3, 'Amit Singh',   '7 STATION ROAD, MAU',     '9000000003', 'AMIT@EXAMPLE.COM',  'DL',       'DL-0000003',    2, 0, 0);
