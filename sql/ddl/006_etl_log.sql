USE StockLab;
GO

IF OBJECT_ID(N'dbo.etl_log', N'U') IS NULL
CREATE TABLE dbo.etl_log(
    id INT IDENTITY(1,1) NOT NULL,
    trade_date DATE NOT NULL,
    status VARCHAR(10) NOT NULL,
    load_count INT NOT NULL,
    error_message NVARCHAR(MAX) NULL,
    created_time DATETIME2(0) NOT NULL CONSTRAINT DF_etl_log_created_time DEFAULT SYSUTCDATETIME(),
    CONSTRAINT PK_etl_log PRIMARY KEY (id),
    CONSTRAINT CK_etl_log_status CHECK (status IN ('SUCCESS', 'FAILED', 'SKIPPED')),
    CONSTRAINT CK_etl_log_load_count CHECK (load_count >= 0),
);
GO
