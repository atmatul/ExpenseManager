from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import extract, func
from sqlalchemy.orm import validates
from datetime import datetime
from models.database import db

DATE_FORMAT = "%Y-%m-%d"
TODAY = datetime.now()

class Expenses(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    expense_date = db.Column(db.Date, nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    from_account = db.Column(db.String(50), nullable=False)
    towards = db.Column(db.String(50), nullable=False)

    def __init__(self, dct_form):
        """
        Init Method
        """
        if self.validate(dct_form):
            self.description = dct_form.get("description", "Empty_Description").strip()
            self.amount = round(float(dct_form.get("amount", "0.00")),2)
            self.expense_date = datetime.strptime(str(dct_form.get("date", "")).strip(), DATE_FORMAT)
            self.booking_date = TODAY
            self.category = str(dct_form.get("category", "Uncategorized")).strip()
            self.from_account = str(dct_form.get("from_account", "")).strip()
            self.towards = str(dct_form.get("towards", "")).strip()
        else:
            raise ValueError

    def __str__(self):
        return f"Eur {self.amount} spend towards {self.towards} for {self.description} on {self.expense_date}"
    
    def validate(self,dct_form) -> bool:
        """
        Validates fields of the form
        """
        if not dct_form.get("description") or not dct_form.get("amount") or not dct_form.get("date"):
            raise ValueError("Required Field Description, Amount or Expense Date not filled")
    
        if float(dct_form.get("amount")) <= 0.0:
            raise ValueError("Amount should be more than Eur 0")
        
        return True
        
def summarize(self) -> list:
    """
    Summary of expense in current month
    """
    pass

def getLastCountRecords(limit=10) -> list:
    """
    List of Last 10 records
    """
    try:
        return list(
            Expenses
            .query
            .order_by(
                Expenses.expense_date.desc(), 
                Expenses.id.desc()
            )
            .limit(limit)
            .all()
        )
    except Exception as e:
        raise Exception(f"Database retrival when wrong\n{e}")
    
def get_current_month_total():
    """
    Calculates the sum of 'amount' for the current calendar month.
    """
    try:
        today = datetime.today()
        
        # Query the sum of amount column
        # Filter where Year and Month match 'today'
        total = (
            db.session
            .query(func.sum(Expenses.amount))
            .filter(
                extract('year', Expenses.expense_date) == today.year,
                extract('month', Expenses.expense_date) == today.month
            )
            .scalar()
        )

        # If no expenses exist, total will be None; return 0.0 instead
        return total if total is not None else 0.0
        
    except Exception as e:
        print(f"Error calculating monthly total: {e}")
        return 0.0