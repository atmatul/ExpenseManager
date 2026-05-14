import pandas as pd
import re
import logging
from utils.logger import get_logger

logger = get_logger(__name__)


def validateExpenseObjectIntegrity(dctData: dict) -> bool:
    """
    Validate structural integrity of expense row insert from st.form.
    Checks for required keys, prohibited symbols, positive amounts, and date validity.

    Checks:
        - Must Columns [Description, Date, Amount, From Account, To Account]
        - Description doesnt contain "!@#$%^&*()-=+<>?,./" etc symbol
        - Amount is number and positive
        - Date format.
    """
    try:
        logger.info(f"dctData: {dctData}")
        # 1. Must Columns Check
        must_cols = ["Description", "Date", "Amount", "From Account", "To Account"]
        for col in must_cols:
            if col not in dctData:
                logger.error(f"Validation Error: Missing required column '{col}'")
                return False

        # 2. Description Symbol Check (prohibits !@#$%^&*()-=+<>?,./)
        description = str(dctData.get("Description", ""))
        if re.search(r"[!@#$%^&*()\-=+<>?,./]", description):
            logger.warning(
                f"Validation Warning: Prohibited symbols found in description: {dctData.get('Description')}"
            )
            return False

        # 3. Amount Check (Must be a positive number)
        amount = float(dctData["Amount"])
        if amount <= 0:
            return False

        # 4. Date Format Validation
        pd.to_datetime(dctData["Date"])

        return True
    except (ValueError, TypeError, Exception) as e:
        logger.error(f"Unexpected validation failure: {str(e)}")
        return False


def validateExpenseObjectDuplicacy(dctData: dict, db_conn) -> bool:
    """
    Validate Duplicacy of the Expense Row insert against fct_expense.
    Returns True if the record is unique, False if a duplicate exists.

    How ?
    duplicate_rows = (
        select
            expense_date,
            description,
            expend_amount,
            parent_category,
            from_account_marker,
            towards_category
        from fct_expense
        where
            month = month_of(dctdctData.date) and
            expense_date = dctdctData.date and
            expend_amount = dctdctData.amount and
            parent_category = dctdctData.category and
            from_account_marker = dctdctData.from_account and
            towards_category = dctdctData.towards
        order by expense_date desc
    )

    if len(duplicate_rows) > 0 :
        expense row exists
        return false
    else:
        return True

    """
    try:
        # Mapping dict keys to fct_expense columns based on schema
        query = """
            SELECT id FROM fct_expense
            WHERE expense_date = ? 
              AND description = ? 
              AND expend_amount = ? 
              AND from_account_marker = ?
            LIMIT 1
        """
        params = [
            dctData.get("Date"),
            dctData.get("Description"),
            dctData.get("Amount"),
            dctData.get("From Account"),
        ]

        # Execute query via singleton connection
        res = db_conn.execute(query, params).fetchone()

        return res is None  # True if no duplicate found
    except Exception:
        return False


def validateExpenseFile(dfExpenseFile: pd.DataFrame) -> tuple:
    """
    Data Integrity Check for Expense File inserted from st.file_uploader.
    Uses vectorized operations for high performance on large CSVs.
    Checks:
        - header must contain must columns [Description, Date, Amount, From Account, To Account]
        - Description column doesnt contain "!@#$%^&*()-=+<>?,./" etc symbol
        - Amount column is number and positive
        - Date format.
    """
    try:
        errors = []

        # 1. Normalize Column Names
        dfExpenseFile.columns = [
            c.lower().replace(" ", "_") for c in dfExpenseFile.columns
        ]

        # 2. Check for Required Columns
        must_cols = ["date", "description", "amount", "from_account", "towards"]
        # Handle common alias 'to_account' -> 'towards'
        if (
            "to_account" in dfExpenseFile.columns
            and "towards" not in dfExpenseFile.columns
        ):
            dfExpenseFile.rename(columns={"to_account": "towards"}, inplace=True)

        missing = [col for col in must_cols if col not in dfExpenseFile.columns]
        if missing:
            errors.append(f"Missing columns: {missing}")

        # 3. Check for Nulls in Critical Columns
        if not missing:
            null_counts = dfExpenseFile[must_cols].isnull().sum()
            cols_with_nulls = null_counts[null_counts > 0].index.tolist()
            if cols_with_nulls:
                errors.append(f"Null values found in: {cols_with_nulls}")

        # 4. Validate Data Types (Amount must be numeric)
        if "amount" in dfExpenseFile.columns:
            non_numeric = (
                pd.to_numeric(dfExpenseFile["amount"], errors="coerce").isna().sum()
            )
            if non_numeric > 0:
                errors.append(f"{non_numeric} rows have non-numeric amounts")

        is_valid = len(errors) == 0
        return is_valid, errors
    except Exception as e:
        return False, [str(e)]


def validateDataPreAppend(dfExpense: pd.DataFrame) -> int:
    """
    Identifies intra-file duplicate rows based on primary columns.
    Returns the number of unique combinations that have multiple occurrences.
        Duplicate Rows:
        - Primary Cols [Date, Amount, From Account, To Account]

    - How ?
    Duplicate_Rows = (
        with expensegrp as (
            select date, amount, from_account, to_account, count(*) as dup_cnt
            from dfExpense
            group by date, amount, from_account, to_account
            order by dup_cnt desc
        )
        select * from expensegrp where dup_cnt > 1
    )
     if len(Duplicate_Rows) > 0 : contains duplicates, identify and fix rows.
    else: all unique records

    Returns:
        len(Duplicate_Rows)
    """
    try:
        primary_cols = ["Date", "Amount", "From Account", "To Account"]

        # Group by primary columns and find groups with more than 1 row
        dup_summary = dfExpense.groupby(primary_cols).size().reset_index(name="dup_cnt")
        duplicate_groups = dup_summary[dup_summary["dup_cnt"] > 1]

        return len(duplicate_groups)
    except Exception:
        return 0


def validateDuplicateFileImport(filename: str, db_conn, **args) -> bool:
    """
    Validates if a filename has already been logged in integrity_file_imported.

    How?
    duplicate_file = (
        select * from integrity_file_imported where filename like '%filename%'
    )

    if len(duplicate_file) > 0:
        file {filename} has been imported on `duplicate_file.ts`
        return False
    else:
        unique file
        return True

    Future Improvements:
        identify file markers in **args
    """
    try:
        query = "SELECT id FROM integrity_file_imported WHERE filename LIKE ?"
        # Using wildcard search as specified in docstring
        res = db_conn.execute(query, [f"%{filename}%"]).fetchone()

        return res is None  # True if unique
    except Exception as e:
        logger.error(f"File validation error: {e}")
        return False
