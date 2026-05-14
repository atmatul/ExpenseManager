from abc import ABC, abstractmethod
import pandas as pd
import os
import traceback
import uuid
from utils.dateutils import DateUtils
from utils.validate import (
    validateExpenseObjectIntegrity,
    validateExpenseObjectDuplicacy,
    validateExpenseFile,
    validateDataPreAppend,
    validateDuplicateFileImport,
)
import duckdb
from utils.logger import get_logger

logger = get_logger(__name__)

# Singleton connection object
DB_PATH = "instance/expenses.db"
db_connection = duckdb.connect(DB_PATH)


class InsertFileObject:
    """
    Insert Object is structured class used to handle multiple cases while inserting file to `expense_line` table.
    """

    def __init__(self, dfExpenses: pd.DataFrame = None, filepath: str = None):
        """
        Has to be invoked with either populated dataframe or valid local FS filepath.
        """
        self.ts = DateUtils.get_now()
        self.abs_file_path = None
        self.filename = None
        self.data = None

        if dfExpenses is not None:
            self.data = dfExpenses
            self.filename = "dataframe_upload"
        elif filepath:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"File not found: {filepath}")
            self.abs_file_path = os.path.abspath(filepath)
            self.filename = os.path.basename(filepath)
            self.data = pd.read_csv(filepath)
        else:
            raise Exception(
                "InsertFileObject requires either a dataframe or a filepath."
            )

        # Markers to be populated by the DBManager/Validators
        self.is_unique = False
        self.has_structural_integrity = False
        self.has_unique_rows = False
        self.structural_errors = []
        self.has_structural_integrity, self.structural_errors = validateExpenseFile(
            self.data
        )


class InsertRowObject:
    """
    Insert Object is structured class used to handle multiple cases while inserting row to `expense_line` table.
    """

    def __init__(self, dctExpenseRow: dict = None):
        """
        Has to be invoked with dict with row of `expenses_line`
        """
        if dctExpenseRow is None:
            raise Exception("Insert row can not be None")
        self.ts = DateUtils.get_now()
        self.has_structural_integrity = False
        self.is_unique = False
        self.data = dctExpenseRow


class BaseDB(ABC):
    """Base DB Class to provide structure to DB Manager."""

    _instance = None
    tbl_expense_line = "expenses_line"

    def __new__(cls):
        if cls._instance is None:
            # Create the singleton instance of the class
            cls._instance = super(BaseDB, cls).__new__(cls)
            # Initialize the connection and schema
            cls._instance.con = db_connection
            cls._instance.initiate()
            cls._instance.populate()
        return cls._instance

    def initiate(self):
        """
        Script to instantiate the DB Schema. Run `create.sql`
        """
        try:
            sql_file = "models/create.sql"
            if os.path.exists(sql_file):
                with open(sql_file, "r") as f:
                    statements = f.read()
                    # DuckDB can execute multiple statements separated by semicolons
                    self.con.execute(statements)
                logger.info("Database tables initialized successfully from create.sql")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
            traceback.print_exc()

    def populate(self):
        """
        Script to populate `expense_line` with seed file.
        """
        try:
            seed_file = "data/seed.csv"
            # Check if table is empty before seeding
            count = self.con.execute(
                f"SELECT COUNT(*) FROM {self.tbl_expense_line}"
            ).fetchone()[0]
            if count == 0 and os.path.exists(seed_file):
                df_seed = pd.read_csv(seed_file)
                # Ensure UUIDs are generated for the seed data
                if "id" not in df_seed.columns:
                    df_seed["id"] = [str(uuid.uuid4()) for _ in range(len(df_seed))]
                self.insertSeed(df_seed)
        except Exception as e:
            print(f"Error during DB Population: {e}")

    def insertSeed(self, data: pd.DataFrame, table: str = "expenses_line"):
        try:
            # Standardize columns to match the 'expenses_line' schema exactly
            # Schema: id, date, description, category, amount, from_account, towards

            # 1. Map Streamlit form keys to DB column names
            mapping = {
                "Date": "date",
                "Description": "description",
                "Amount": "amount",
                "From Account": "from_account",
                "To Account": "towards",
                "Category": "category",  # Ensure category is included
            }

            df_to_insert = data.rename(columns=mapping)

            # 2. Add missing columns with defaults
            if "id" not in df_to_insert.columns:
                df_to_insert["id"] = [
                    str(uuid.uuid4()) for _ in range(len(df_to_insert))
                ]

            if "category" not in df_to_insert.columns:
                # Default to 'Uncategorized' if not provided in manual form
                df_to_insert["category"] = "Uncategorized"

            # 3. Explicitly Cast Types to prevent Conversion Errors
            df_to_insert["amount"] = pd.to_numeric(
                df_to_insert["amount"], errors="coerce"
            ).fillna(0.0)
            df_to_insert["date"] = pd.to_datetime(df_to_insert["date"]).dt.date

            # 4. Ensure column order matches the table definition in create.sql
            cols = [
                "id",
                "date",
                "description",
                "category",
                "amount",
                "from_account",
                "towards",
            ]
            df_to_insert = df_to_insert[cols]

            self.con.append(table, df_to_insert)
            logger.info(f"Successfully appended {len(df_to_insert)} rows to {table}")

            # Trigger the ETL to fct_expense
            self.ingest_fct_expense()
            return True
        except Exception as e:
            logger.error(f"Insert failed: {str(e)}", exc_info=True)
            return False

    def export(self, format: str = "csv"):
        """
        Export all the tables in `create.sql` as csv/parquet etc.
        """
        try:
            tables = self.con.execute("SHOW TABLES").fetchall()
            for (table_name,) in tables:
                export_path = f"data/export_{table_name}_{DateUtils.get_today_date().replace("-","_")}.{format}"
                if format.lower() == "csv":
                    self.con.execute(
                        f"COPY {table_name} TO '{export_path}' (HEADER, DELIMITER ',')"
                    )
                elif format.lower() == "parquet":
                    self.con.execute(
                        f"COPY {table_name} TO '{export_path}' (FORMAT PARQUET)"
                    )
                print(f"Exported {table_name} to {export_path}")
        except Exception as e:
            print(f"Export failed: {e}")

    def ingest_fct_expense(self):
        """
        ETL: Uplift expenses_line to fct_expense with schema mapping.
        """
        try:
            # Transformation logic using DuckDB SQL for performance
            # Change the date extraction lines to include explicit casting:
            logger.info("Starting ETL: Uplifting expenses_line to fct_expense")

            self.con.execute("BEGIN TRANSACTION;")
            self.con.execute("DELETE FROM fct_expense;")

            sql = """
            INSERT INTO fct_expense
            SELECT 
                id,
                CAST(date AS DATE) as expense_date,
                current_date as booked_date,
                now() as last_modified_at,
                description,
                category as parent_category,
                NULL as sub_category,
                NULL as category_tag,
                amount as expend_amount,
                'EUR' as currency,
                from_account as from_account_marker,
                towards as towards_category,
                NULL as towards_sub_category,
                NULL as towards_category_tag,
                day(CAST(date AS DATE)) as day_of_month,
                month(CAST(date AS DATE)) as month,
                year(CAST(date AS DATE)) as year,
                (year(CAST(date AS DATE)) * 100 + month(CAST(date AS DATE))) as month_year,
                strftime(CAST(date AS DATE), '%b-%y') as month_year_marker,
                dayofweek(CAST(date AS DATE)) as num_day_of_week,
                dayname(CAST(date AS DATE)) as day_of_week,
                CASE 
                    WHEN month(CAST(date AS DATE)) IN (12, 1, 2) THEN 'Winter'
                    WHEN month(CAST(date AS DATE)) IN (3, 4, 5) THEN 'Spring'
                    WHEN month(CAST(date AS DATE)) IN (6, 7, 8) THEN 'Summer'
                    ELSE 'Autumn' 
                END as season
            FROM expenses_line;
            """

            self.con.execute(sql)
            self.con.execute("COMMIT;")
            logger.info("ETL successful: fct_expense refreshed.")
        except Exception as e:
            logger.error(f"ETL Ingestion failed: {str(e)}", exc_info=True)

    @abstractmethod
    def insert(self, data: pd.DataFrame) -> bool:
        """
        Insert pd.Dataframe to `expenses_line`
        """
        pass


class DBManager(BaseDB):
    """App DB Manager ORM Layer."""

    def __init__(self):
        # super().__init__() is called via BaseDB.__new__ logic
        pass

    def insert(self, data: pd.DataFrame) -> bool:
        """Surgical Fix: Map UI keys to DB columns and ensure correct order."""
        try:
            # 1. Map Streamlit form keys to DB column names
            mapping = {
                "Date": "date",
                "Description": "description",
                "Amount": "amount",
                "Category": "category",
                "From Account": "from_account",
                "To Account": "towards",
            }
            df_to_insert = data.rename(columns=mapping)

            # 2. Add UUIDs and defaults
            if "id" not in df_to_insert.columns:
                df_to_insert["id"] = [
                    str(uuid.uuid4()) for _ in range(len(df_to_insert))
                ]
            if "category" not in df_to_insert.columns:
                df_to_insert["category"] = "Uncategorized"

            if "to_account" in df_to_insert.columns:
                df_to_insert.rename(columns={"to_account": "towards"}, inplace=True)

            # 3. Explicit Casting
            df_to_insert["amount"] = pd.to_numeric(
                df_to_insert["amount"], errors="coerce"
            ).fillna(0.0)
            df_to_insert["date"] = pd.to_datetime(
                df_to_insert.get("date", DateUtils.get_today_date())
            ).dt.date

            # 4. REORDER: Must match expenses_line schema: id, date, description, category, amount, from_account, towards
            expected_order = [
                "id",
                "date",
                "description",
                "category",
                "amount",
                "from_account",
                "towards",
            ]
            df_to_insert = df_to_insert[expected_order]

            self.con.append(self.tbl_expense_line, df_to_insert)
            self.ingest_fct_expense()  # Sync Silver layer
            return True
        except Exception as e:
            logger.error(f"Insert failed: {e}")
            return False

    def insertExpenseFile(self, file_obj: InsertFileObject) -> int:
        """Append Insert rows of `InsertFileObject.data` into `expenses_line`
        How ?
        insert_obj = {
                ts: timestamp of insert call (good to avoid duplicates),
                filename: upload_file_name
                validate_unique_file: True/False,
                validated_structure: True/False,
                validated_duplicates: True/False,
                data_obj: pd.Dataframe
        }
        if all(validate_unique_file, validated_structure, validated_duplicates):
            insert data_obj to expenses_line
            insert file_markers to integrity_file_imported
        else:
            raise IntegrityError based on which ever value in if is False.

        Returns : no of impacted rows in table `expenses_line`
        0 if action fails
        """

        try:
            # 1. Run Validations
            file_obj.is_unique = validateDuplicateFileImport(
                file_obj.filename, self.con
            )
            file_obj.has_structural_integrity = validateExpenseFile(file_obj.data)
            file_obj.has_unique_rows = validateDataPreAppend(file_obj.data) == 0

            if not file_obj.has_structural_integrity:
                # EXPLICIT LOGGING: Loop through the list of errors generated in validate.py
                for error in file_obj.structural_errors:
                    logger.error(
                        f"FILE INTEGRITY FAILURE [{file_obj.filename}]: {error}"
                    )

                raise duckdb.IntegrityError(
                    f"Structural integrity failed: {file_obj.structural_errors}"
                )

            if not file_obj.is_unique:
                logger.error(
                    f"FILE DUPLICATION: {file_obj.filename} has already been processed."
                )
                raise duckdb.IntegrityError("Duplicate file detected")

            # 2. Integrity Guardrail
            if all(
                [
                    file_obj.is_unique,
                    file_obj.has_structural_integrity,
                    file_obj.has_unique_rows,
                ]
            ):
                row_count = len(file_obj.data)
                if self.insert(file_obj.data):
                    # Log file import marker
                    marker_data = pd.DataFrame(
                        [
                            {
                                "id": str(uuid.uuid4()),
                                "ts": file_obj.ts,
                                "filename": file_obj.filename,
                                "date_imported": DateUtils.get_now().strftime(
                                    "%Y-%m-%d"
                                ),
                                "no_of_rows_imported": row_count,
                            }
                        ]
                    )
                    self.con.append("integrity_file_imported", marker_data)
                    return row_count
            else:
                # Identify which validation failed for the error message
                error_msg = []
                if not file_obj.is_unique:
                    error_msg.append("File already imported")
                if not file_obj.has_structural_integrity:
                    error_msg.append("Structural integrity failed")
                if not file_obj.has_unique_rows:
                    error_msg.append("Duplicate rows detected within file")
                raise duckdb.IntegrityError(f"Row Insert Blocked: {error_msg}")

        except duckdb.IntegrityError as ie:
            logger.error(f"Insert aborted: {str(ie)}")
            return 0
        except Exception as e:
            print(f"insertExpenseFile Error: {e}")
            return 0

    def insertExpenseRow(self, row_obj: InsertRowObject) -> int:
        """Append 1 row of `InsertRowObject.data` into `expenses_line`

        `InsertRowObject.data` is a dict with all must keys available and valid:
            - validate.validateExpenseObjectIntegrity => True
            - validate.validateExpenseObjectDuplicacy => True

        How ?
        insert_row = {
            ts: timestamp of insert call (good to avoid duplicates),
            validate_structural_integirty : True/False,
            validated_duplicates: True/False,
            data_obj: dict
        }

        if all(validate_structural_integirty, validated_duplicates):
            convert row to pd.Dataframe
            insert data_obj to expenses_line
        else:
            raise IntegrityError based on which ever value in if is False.

        Returns : no of impacted rows in table `expenses_line`
        0 if action fails
        """
        logger.info(f"Attempting manual row insert: {row_obj.data.get('Description')}")
        try:
            # 1. Run Validations
            row_obj.has_structural_integrity = validateExpenseObjectIntegrity(
                row_obj.data
            )
            row_obj.is_unique = validateExpenseObjectDuplicacy(row_obj.data, self.con)

            # 2. Logic execution
            if not row_obj.has_structural_integrity:
                logger.warning("Insert rejected: Structural integrity check failed.")
                raise duckdb.IntegrityError("Row Insert Blocked: Integrity violation")
            if not row_obj.is_unique:
                logger.warning("Insert rejected: Duplicate record detected.")
                raise duckdb.IntegrityError("Row Insert Blocked: Duplicate record")

            if row_obj.has_structural_integrity and row_obj.is_unique:
                df_row = pd.DataFrame([row_obj.data])
                if self.insert(df_row):
                    return 1
            else:
                error_msg = (
                    "Integrity violation"
                    if not row_obj.has_structural_integrity
                    else "Duplicate record"
                )
                raise duckdb.IntegrityError(
                    f"Row Insert Blocked: {error_msg}", params=None, orig=None
                )

        except duckdb.IntegrityError as ie:
            # Catch known integrity errors gracefully
            logger.error(f"Insert aborted: {str(ie)}")
            return 0
        except Exception as e:
            logger.error(f"insertExpenseRow unexpected error: {e}", exc_info=True)
            return 0


# Singleton global instance
dbManager = DBManager()
