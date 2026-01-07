-- HF Parser Database Initialization Script
-- Run this script with MySQL root user to create database and user

-- Create database
CREATE DATABASE IF NOT EXISTS hf_tracker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user (if not exists)
CREATE USER IF NOT EXISTS 'hf_user'@'localhost' IDENTIFIED BY 'Abcd1234#';

-- Grant all privileges
GRANT ALL PRIVILEGES ON hf_tracker.* TO 'hf_user'@'localhost';

-- Flush privileges
FLUSH PRIVILEGES;

-- Verify database
USE hf_tracker;
SELECT 'Database hf_tracker created successfully!' AS status;
SELECT USER, HOST FROM mysql.user WHERE USER = 'hf_user';
