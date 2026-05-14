-- 1. Metadata for file ingestion tracking
CREATE OR REPLACE TABLE integrity_file_imported (
    id UUID PRIMARY KEY,
    ts TIMESTAMP,
    filename TEXT,
    date_imported TEXT,
    no_of_rows_imported INTEGER
);

-- 2. Bronze Layer: Raw data landing
CREATE OR REPLACE TABLE expenses_line (
    id UUID PRIMARY KEY,
    date DATE,
    description TEXT,
    category TEXT,
    amount DOUBLE,
    from_account TEXT,
    towards TEXT
);

-- 3. Silver/Gold Layer: Fact table with analytical dimensions
CREATE OR REPLACE TABLE fct_expense (
    id UUID PRIMARY KEY,
    expense_date DATE,
    booked_date DATE,
    last_modified_at TIMESTAMP,
    description TEXT,
    parent_category TEXT,
    sub_category TEXT,
    category_tag TEXT,
    expend_amount DOUBLE,
    currency TEXT,
    from_account_marker TEXT,
    towards_category TEXT,
    towards_sub_category TEXT,
    towards_category_tag TEXT,
    day_of_month INTEGER,
    month INTEGER,
    year INTEGER,
    month_year INTEGER,
    month_year_marker TEXT,
    num_day_of_week INTEGER,
    day_of_week TEXT,
    season TEXT
);

-- 4. Account Dimension
CREATE OR REPLACE TABLE dim_account (
    id UUID PRIMARY KEY,
    name TEXT,
    tag TEXT,
    marker TEXT,
    type TEXT,
    minimum_balance_per_bank DOUBLE,
    minimum_balance_per_self DOUBLE,
    current_balance DOUBLE,
    currency TEXT
);

-- Replace the problematic INSERT OR IGNORE with this:
INSERT INTO dim_account (id, name, tag, marker, type, minimum_balance_per_bank, minimum_balance_per_self, current_balance, currency)
SELECT uuid(), 'N26', 'atul,cc,prepaid', 'n26', 'general expense', 0.0, 10.0, 80.0, 'EUR'
WHERE NOT EXISTS (SELECT 1 FROM dim_account WHERE marker = 'n26');

INSERT INTO dim_account (id, name, tag, marker, type, minimum_balance_per_bank, minimum_balance_per_self, current_balance, currency)
SELECT uuid(), 'Wise', 'atul,cc,prepaid', 'wise', 'fat expense', 0.0, 100.0, 730.0, 'EUR'
WHERE NOT EXISTS (SELECT 1 FROM dim_account WHERE marker = 'wise');

-- Replace the problematic INSERT OR IGNORE with this:
INSERT INTO dim_account (id, name, tag, marker, type, minimum_balance_per_bank, minimum_balance_per_self, current_balance, currency)
SELECT uuid(), 'Deutsche Bank', 'atul,db,salary', 'deutsche_bank', 'salary', 100.0,1000.0, 7300.0, 'EUR'
WHERE NOT EXISTS (SELECT 1 FROM dim_account WHERE marker = 'deutsche_bank');

INSERT INTO dim_account (id, name, tag, marker, type, minimum_balance_per_bank, minimum_balance_per_self, current_balance, currency)
SELECT uuid(), 'ICICI', 'atul,amazon_card,postpaid', 'icici', 'eccomerce', 0.0, 0.0, 7300.0, 'INR'
WHERE NOT EXISTS (SELECT 1 FROM dim_account WHERE marker = 'icici');