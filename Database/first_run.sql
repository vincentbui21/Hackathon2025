-- Create the database
CREATE DATABASE IF NOT EXISTS valioaimo;
USE valioaimo;

-- ========================================
-- Table: Producer
-- ========================================
CREATE TABLE IF NOT EXISTS Producer (
    ProducerID INT PRIMARY KEY,
    Producer_name VARCHAR(255) NOT NULL,
    Credit_score DECIMAL(5,2) DEFAULT 0.0
);

-- ========================================
-- Table: Product
-- ========================================
CREATE TABLE IF NOT EXISTS Product (
    ProductID INT  PRIMARY KEY,
    ProducerID INT NOT NULL,
    Product_name VARCHAR(255) NOT NULL,
    Price DECIMAL(10,2) NOT NULL,
    Quantity INT DEFAULT 500,
    Allergens JSON,
    Non_allergens JSON,
    Prediction_score DECIMAL(5,2) DEFAULT 0.0,
    FOREIGN KEY (ProducerID) REFERENCES Producer(ProducerID) ON DELETE CASCADE
);

-- ========================================
-- Table: `Order`
-- ========================================
CREATE TABLE IF NOT EXISTS `Order` (
    OrderID INT AUTO_INCREMENT PRIMARY KEY,
    Total DECIMAL(10,2) DEFAULT 0.0,
    Status VARCHAR(50) DEFAULT 'Pending',
    Tracking JSON,
    Substitution JSON
);

-- Optional: index on Tracking/Substitution if you query often

