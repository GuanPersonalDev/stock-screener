USE StockLab;
GO

IF OBJECT_ID(N'dbo.crawl_status', N'U') IS NULL
CREATE TABLE dbo.crawl_status(
    dataset VARCHAR(50) NOT NULL,
    trade_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,
    CONSTRAINT PK_crawl_status PRIMARY KEY (dataset, trade_date),
    CONSTRAINT CK_crawl_status_status CHECK (status IN ('SUCCESS', 'NO_DATA', 'FAILED'))
);
GO
