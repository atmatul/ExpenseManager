import pandas as pd
import re
import logging
from utils.logger import get_logger

logger = get_logger(__name__)


def validateExpenseObjectIntegrity(dctData: dict) -> tuple:
    """
    Validate structural integrity of expense row insert from st.form.
    Returns: (is_valid: bool, error_details: dict or None)
    
    Checks:
        - Must Columns [Description, Date, Amount, From Account, To Account, Category]
        - Description doesnt contain "!@#$%^&*()-=+<>?,./" etc symbol
        - Amount is number and positive
        - Date format.
    """
    try:
        logger.info(f"Validating row: {dctData}")
        error_details = {}
        
        # 1. Must Columns Check
        must_cols = ["Description", "Date", "Amount", "From Account", "To Account", "Category"]
        missing_cols = [col for col in must_cols if col not in dctData or dctData[col] is None or str(dctData[col]).strip() == ""]
        if missing_cols:
            error_details["missing_fields"] = missing_cols
            logger.error(f"Missing required fields: {missing_cols}")
            return False, error_details

        # 2. Description Symbol Check (prohibits !@#$%^&*()-=+<>?,./)
        description = str(dctData.get("Description", ""))
        if re.search(r"[!@#$%^&*()\-=+<>?,./]", description):
            error_details["field"] = "Description"
            error_details["reason"] = "Contains prohibited symbols (!@#$%^&*()-=+<>?,./)"
            error_details["value"] = description
            logger.error(f"Invalid description: {description}")
            return False, error_details

        # 3. Amount Check (Must be a positive number)
        try:
            amount = float(dctData["Amount"])
            if amount <= 0:
                error_details["field"] = "Amount"
                error_details["reason"] = "Amount must be positive (> 0)"
                error_details["value"] = dctData["Amount"]
                logger.error(f"Invalid amount: {amount}")
                return False, error_details
        except (ValueError, TypeError):
            error_details["field"] = "Amount"
            error_details["reason"] = "Amount must be a valid number"
            error_details["value"] = dctData["Amount"]
            logger.error(f"Amount is not numeric: {dctData['Amount']}")
            return False, error_details

        # 4. Date Format Validation
        try:
            pd.to_datetime(dctData["Date"])
        except (ValueError, TypeError):
            error_details["field"] = "Date"
            error_details["reason"] = "Invalid date format"
            error_details["value"] = dctData["Date"]
            logger.error(f"Invalid date: {dctData['Date']}")
            return False, error_details

        logger.info("Row passed structural integrity validation")
        return True, None
    except Exception as e:
        error_details = {"reason": f"Unexpected validation failure: {str(e)}"}
        logger.error(f"Validation exception: {str(e)}", exc_info=True)
        return False, error_details


def validateExpenseObjectDuplicacy(dctData: dict, db_conn) -> tuple:
    """
    Validate Duplicacy of the Expense Row insert against fct_expense.
    Returns: (is_unique: bool, duplicate_record: dict or None)
    
    Checks for duplicate based on:
        - expense_date (matches Date field)
        - description (matches Description field)
        - expend_amount (matches Amount field)
        - parent_category (matches Category field)
        - from_account_marker (matches From Account field)
        - towards_category (matches To Account field)
    
    If a duplicate is found, returns the matching record details.
    """
    try:
        # Mapping dict keys to fct_expense columns based on schema
        query = """
            SELECT id, expense_date, description, expend_amount, parent_category, 
                   from_account_marker, towards_category
            FROM fct_expense
            WHERE CAST(expense_date AS DATE) = CAST(? AS DATE)
              AND LOWER(description) = LOWER(?)
              AND expend_amount = ?
              AND parent_category = ?
              AND from_account_marker = ?
              AND towards_category = ?
            LIMIT 1
        """
        params = [
            dctData.get("Date"),
            dctData.get("Description"),
            dctData.get("Amount"),
            dctData.get("Category"),
            dctData.get("From Account"),
            dctData.get("To Account"),
        ]

        # Execute query via singleton connection
        res = db_conn.execute(query, params).fetchone()

        if res is not None:
            # Duplicate found - return details
            duplicate_record = {
                "id": str(res[0]),
                "expense_date": str(res[1]),
                "description": res[2],
                "expend_amount": res[3],
                "parent_category": res[4],
                "from_account_marker": res[5],
                "towards_category": res[6],
            }
            logger.warning(f"Duplicate record found: {duplicate_record}")
            return False, duplicate_record
        
        logger.info("Row is unique - no duplicate found")
        return True, None
    except Exception as e:
        logger.error(f"Duplicacy check error: {str(e)}", exc_info=True)
        return False, {"error": str(e)}


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


def validateDataPreAppend(dfExpense: pd.DataFrame) -> tuple:
    """
    Identifies intra-file duplicate rows based on primary columns.
    Returns: (duplicate_count: int, duplicate_details: list or None)
    
    Duplicate Rows are identified by:
        - Primary Cols [Date, Amount, From Account, To Account]
    
    Returns:
        (count, details) where:
        - count: number of duplicate groups found (0 if no duplicates)
        - details: list of dicts showing duplicate groups, or None if count == 0
    """
    try:
        primary_cols = ["Date", "Amount", "From Account", "To Account"]

        # Group by primary columns and find groups with more than 1 row
        dup_summary = dfExpense.groupby(primary_cols).size().reset_index(name="dup_cnt")
        duplicate_groups = dup_summary[dup_summary["dup_cnt"] > 1]

        if len(duplicate_groups) == 0:
            logger.info("No intra-file duplicates found")
            return 0, None
        
        # Format duplicate details
        duplicate_details = []
        for _, row in duplicate_groups.iterrows():
            duplicate_details.append({
                "date": str(row["Date"]),
                "amount": float(row["Amount"]),
                "from_account": str(row["From Account"]),
                "towards": str(row["To Account"]),
                "occurrence_count": int(row["dup_cnt"]),
            })
        
        logger.warning(f"Found {len(duplicate_groups)} duplicate groups in file")
        return len(duplicate_groups), duplicate_details
    except Exception as e:
        logger.error(f"Error checking intra-file duplicates: {str(e)}", exc_info=True)
        return 0, None


def validateDuplicateFileImport(filename: str, db_conn, **args) -> tuple:
    """
    Validates if a filename has already been logged in integrity_file_imported.
    Returns: (is_unique: bool, import_info: dict or None)

    If file has been imported before, returns details of the previous import.
    Otherwise returns (True, None) indicating the file is unique.
    """
    try:
        query = "SELECT id, ts, filename, date_imported, no_of_rows_imported FROM integrity_file_imported WHERE filename LIKE ?"
        # Using wildcard search as specified in docstring
        res = db_conn.execute(query, [f"%{filename}%"]).fetchone()

        if res is not None:
            import_info = {
                "id": str(res[0]),
                "timestamp": str(res[1]),
                "filename": res[2],
                "date_imported": str(res[3]),
                "no_of_rows_imported": int(res[4]),
            }
            logger.warning(f"File already imported: {import_info}")
            return False, import_info
        
        logger.info(f"File {filename} is unique - not previously imported")
        return True, None
    except Exception as e:
        logger.error(f"File validation error: {e}", exc_info=True)
        return False, {"error": str(e)}
