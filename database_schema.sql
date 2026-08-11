CREATE DATABASE IF NOT EXISTS nativeframes
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE nativeframes;

CREATE TABLE IF NOT EXISTS viewers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    mobile VARCHAR(30) NULL,
    login_count INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME NULL
);

CREATE TABLE IF NOT EXISTS viewer_logins (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    viewer_id INT NOT NULL,
    login_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(80) NULL,
    user_agent VARCHAR(255) NULL,
    FOREIGN KEY (viewer_id) REFERENCES viewers(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS media (
    id INT AUTO_INCREMENT PRIMARY KEY,
    media_type ENUM('photo','video','text') NOT NULL,
    file_name VARCHAR(255) NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NULL,
    is_favorite TINYINT(1) NOT NULL DEFAULT 0,
    is_deleted TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin_profile (
    id INT PRIMARY KEY,
    name VARCHAR(150) DEFAULT 'NativeFrames',
    username VARCHAR(120) DEFAULT 'nativeframes',
    dob DATE NULL,
    mobile VARCHAR(40) NULL,
    email VARCHAR(180) NULL,
    location VARCHAR(180) NULL,
    occupation VARCHAR(180) NULL,
    about TEXT NULL,
    profile_photo VARCHAR(255) NULL
);

INSERT INTO admin_profile (id, name, username)
VALUES (1, 'NativeFrames', 'nativeframes')
ON DUPLICATE KEY UPDATE username = VALUES(username);
