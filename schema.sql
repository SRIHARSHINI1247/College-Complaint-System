-- Run on RDS MySQL (optional: the app also creates tables automatically)
CREATE DATABASE IF NOT EXISTS complaintdb;
USE complaintdb;
CREATE TABLE user (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(120) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(10) DEFAULT 'student'
);
CREATE TABLE complaint (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  category VARCHAR(30) NOT NULL,
  location VARCHAR(100) NOT NULL,
  description TEXT NOT NULL,
  status VARCHAR(20) DEFAULT 'Submitted',
  assigned_to VARCHAR(100),
  remarks TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user(id)
);
