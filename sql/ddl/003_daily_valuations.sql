USE StockLab;
GO

IF OBJECT_ID(N'dbo.daily_valuations', N'U') IS NULL
CREATE TABLE dbo.daily_valuations(
    stock_id VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    price_to_earnings_ratio DECIMAL(10,2) NULL,   
    dividend_yield DECIMAL(10,2) NULL,
    price_to_book_ratio DECIMAL(10,2) NULL,
    CONSTRAINT PK_daily_valuations PRIMARY KEY (stock_id, trade_date),
    CONSTRAINT FK_daily_valuations_stocks FOREIGN KEY (stock_id) REFERENCES dbo.stocks(stock_id),
    CONSTRAINT CK_daily_valuations_price_to_earnings_ratio CHECK (price_to_earnings_ratio >=0),
    CONSTRAINT CK_daily_valuations_dividend_yield CHECK (dividend_yield >=0),
    CONSTRAINT CK_daily_valuations_price_to_book_ratio CHECK (price_to_book_ratio >=0)
);

GO
