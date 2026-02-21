-- Spend Wise Database Schema
-- MySQL Database Migration Script

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS spend_wise;
USE spend_wise;

-- Users table
CREATE TABLE IF NOT EXISTS user (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone_number VARCHAR(20),
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Categories table (for expense categorization)
CREATE TABLE IF NOT EXISTS category (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    user_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
);

-- Expenses table
CREATE TABLE IF NOT EXISTS expense (
    id INT AUTO_INCREMENT PRIMARY KEY,
    amount DECIMAL(10, 2) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    date DATE NOT NULL,
    user_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
);

-- Budgets table
CREATE TABLE IF NOT EXISTS budget (
    id INT AUTO_INCREMENT PRIMARY KEY,
    amount DECIMAL(10, 2) NOT NULL,
    category VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    user_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
);

-- Income table
CREATE TABLE IF NOT EXISTS income (
    id INT AUTO_INCREMENT PRIMARY KEY,
    amount DECIMAL(10, 2) NOT NULL,
    source VARCHAR(100) NOT NULL,
    description TEXT,
    date DATE NOT NULL,
    user_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notification (
    id INT AUTO_INCREMENT PRIMARY KEY,
    notification_type ENUM('budget_warning', 'budget_exceeded', 'income_reminder', 'expense_alert', 'system') NOT NULL,
    message TEXT NOT NULL,
    user_id INT NOT NULL,
    sent BOOLEAN DEFAULT FALSE,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE
);

-- Insert default categories
INSERT IGNORE INTO category (name, description) VALUES 
('Food', 'Food and dining expenses'),
('Transportation', 'Transportation and travel'),
('Entertainment', 'Entertainment and leisure'),
('Shopping', 'Shopping and personal items'),
('Bills', 'Utilities and bills'),
('Healthcare', 'Medical and healthcare'),
('Education', 'Education and learning'),
('Other', 'Miscellaneous expenses');

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_expense_user_date ON expense(user_id, date);
CREATE INDEX IF NOT EXISTS idx_expense_category ON expense(category);
CREATE INDEX IF NOT EXISTS idx_budget_user_category ON budget(user_id, category);
CREATE INDEX IF NOT EXISTS idx_income_user_date ON income(user_id, date);
CREATE INDEX IF NOT EXISTS idx_notification_user_read ON notification(user_id, read);

-- Create a sample admin user (password: admin123)
INSERT IGNORE INTO user (username, password, email, first_name, last_name, role) VALUES 
('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'admin@spendwise.com', 'Admin', 'User', 'admin');
