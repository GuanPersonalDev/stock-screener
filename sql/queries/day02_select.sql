USE StockLab;
GO

DROP TABLE IF EXISTS practice_stocks;
GO

CREATE TABLE practice_stocks(
    stock_id    VARCHAR(10)     NOT NULL,
    stock_name  NVARCHAR(50)    NOT NULL,
    industry    NVARCHAR(50)    NOT NULL,
    close_price DECIMAL(10, 2)  NOT NULL,
    listed_date DATE            NOT NULL,
    dividend    DECIMAL(10, 2)  NULL
);
GO

SELECT name FROM sys.tables;

INSERT INTO practice_stocks (stock_id, stock_name, industry, close_price, listed_date, dividend)
VALUES
    ('2330', N'台積電', N'半導體',   1000.00, '1994-09-05', 18.00),
    ('2454', N'聯發科', N'半導體',   1200.00, '2001-07-23', 54.00),
    ('2303', N'聯電',   N'半導體',     50.00, '1985-07-16', NULL),
    ('2317', N'鴻海',   N'電子代工',  180.00, '1991-06-18', 5.40),
    ('2382', N'廣達',   N'電子代工',  280.00, '1999-01-08', 14.50),
    ('3231', N'緯創',   N'電子代工',  110.00, '2003-08-19', NULL),
    ('2881', N'富邦金', N'金融',       85.00, '2001-12-19', 3.00),
    ('2882', N'國泰金', N'金融',       65.00, '2001-12-31', 2.00),
    ('2891', N'中信金', N'金融',       40.00, '2002-05-17', 1.40),
    ('2412', N'中華電', N'通信網路',  125.00, '2000-10-27', 4.70);
GO

SELECT * FROM practice_stocks;

SELECT stock_id, stock_name, close_price
FROM practice_stocks
WHERE close_price BETWEEN 50 AND 200
ORDER BY close_price;

SELECT stock_id, stock_name, industry
FROM practice_stocks
WHERE industry IN (N'半導體', N'金融');

SELECT stock_id, stock_name
FROM practice_stocks
WHERE stock_name LIKE N'%金%';

SELECT TOP 3 stock_id, stock_name, close_price
FROM practice_stocks
ORDER BY close_price DESC;

SELECT industry,
    COUNT(*)   AS stock_count,
    AVG(close_price) AS avg_price
FROM practice_stocks
GROUP BY industry
ORDER BY avg_price DESC;

SELECT stock_name, close_price,
    CASE
        WHEN close_price >= 500 THEN N'高價股'
        WHEN close_price >= 100 THEN N'中價股'
        ELSE N'低價股'
    END AS price_level
FROM practice_stocks
ORDER BY close_price DESC;

SELECT industry,
    AVG(close_price) AS avg_price
FROM practice_stocks
GROUP BY industry
HAVING AVG(close_price) > 100;

SELECT stock_name, industry, close_price
FROM practice_stocks
WHERE industry IN (
    SELECT industry
    FROM practice_stocks
    GROUP BY industry
    HAVING AVG(close_price) > 100
);

SELECT COUNT(*) AS total_rows,
    COUNT(dividend) AS row_with_dividend
FROM practice_stocks;

SELECT stock_name
FROM practice_stocks
WHERE dividend IS NULL;

SELECT 0.1E0 + 0.2E0 AS float_sum,
    CASE WHEN 0.1E0 + 0.2E0 = 0.3E0 THEN N'相等' ELSE N'不相等' END AS float_check,
    CAST(0.1E0 + 0.2E0 AS DECIMAL(20, 17)) AS float_real_value;

SELECT 0.1 + 0.2 AS decimal_sum,
    CASE WHEN 0.1 + 0.2 = 0.3 THEN N'相等' ELSE N'不相等' END AS decimal_check;

