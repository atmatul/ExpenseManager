from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
import traceback

db = SQLAlchemy()


class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def insert(self, data_row):
        """Generic insert for any Model object."""
        try:
            db.session.add(data_row)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print("--- DATABASE CRASH LOG ---")
            traceback.print_exc()  # This prints the full stack trace to the terminal
            print("--------------------------")
            raise e

    def delete(self, model_class, record_id):
        """Generic delete by ID."""
        try:
            record = model_class.query.get_or_404(record_id)
            if record:
                db.session.delete(record)
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            raise e
