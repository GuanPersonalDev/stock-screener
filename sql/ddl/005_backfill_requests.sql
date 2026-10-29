USE StockLab;
GO

IF OBJECT_ID(N'dbo.backfill_requests', N'U') IS NULL
CREATE TABLE dbo.backfill_requests(
    id INT IDENTITY(1,1) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_force_backfill BIT NOT NULL CONSTRAINT DF_backfill_requests_is_force_backfill DEFAULT 0,
    status VARCHAR(10) NOT NULL,
    created_time DATETIME2(0) NOT NULL CONSTRAINT DF_backfill_requests_created_time DEFAULT SYSUTCDATETIME(),
    finished_time DATETIME2(0) NULL,
    CONSTRAINT PK_backfill_requests PRIMARY KEY (id),
    CONSTRAINT CK_backfill_requests_status CHECK (status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')),
    CONSTRAINT CK_backfill_requests_end_date CHECK (end_date >= start_date)
);
GO
