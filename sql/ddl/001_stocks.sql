USE StockLab;
GO

IF OBJECT_ID(N'dbo.stocks', N'U') IS NULL
CREATE TABLE dbo.stocks(
    stock_id VARCHAR(10) NOT NULL,
    stock_name NVARCHAR(50) NOT NULL,
    industry NVARCHAR(50) NULL,
    market NVARCHAR(50) NOT NULL,
    security_type VARCHAR(10) NOT NULL,
    listing_status VARCHAR(10) NOT NULL CONSTRAINT DF_stocks_listing_status DEFAULT 'LISTED',
    CONSTRAINT PK_stocks PRIMARY KEY (stock_id),
    CONSTRAINT CK_stocks_security_type CHECK (security_type IN ('STOCK', 'ETF', 'BOND_ETF')),
    CONSTRAINT CK_stocks_listing_status CHECK (listing_status IN ('LISTED', 'DELISTED')),
    CONSTRAINT CK_stocks_market CHECK (market IN ('TWSE', 'TPEX', 'EMERGING'))
);

GO
