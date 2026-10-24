USE StockLab;
GO

IF OBJECT_ID(N'dbo.daily_prices', N'U') IS NULL
CREATE TABLE dbo.daily_prices(
    stock_id VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    open_price DECIMAL(10, 2) NULL,
    high_price DECIMAL(10, 2) NULL,
    low_price DECIMAL(10, 2) NULL,
    close_price DECIMAL(10, 2) NULL,
    trade_volume BIGINT NOT NULL,
    trade_value BIGINT NOT NULL,
    CONSTRAINT PK_daily_prices PRIMARY KEY (stock_id, trade_date),
    CONSTRAINT FK_daily_prices_stocks FOREIGN KEY (stock_id) REFERENCES dbo.stocks(stock_id),
    CONSTRAINT CK_daily_prices_open_price CHECK (open_price >=0),
    CONSTRAINT CK_daily_prices_high_low CHECK (high_price >=low_price),
    CONSTRAINT CK_daily_prices_low_price CHECK (low_price >=0),
    CONSTRAINT CK_daily_prices_close_price CHECK (close_price >=0),
    CONSTRAINT CK_daily_prices_trade_volume CHECK (trade_volume >=0),
    CONSTRAINT CK_daily_prices_trade_value CHECK (trade_value >=0)
);
GO
