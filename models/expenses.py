from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import extract, func
from sqlalchemy.orm import validates
from datetime import datetime
from models.database import db
from utils.dateutils import DateUtils

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
            self.amount = round(float(dct_form.get("amount", "0.00")), 2)
            self.expense_date = datetime.strptime(
                str(dct_form.get("date", "")).strip(), DATE_FORMAT
            )
            self.booking_date = TODAY
            self.category = str(dct_form.get("category", "Uncategorized")).strip()
            self.from_account = str(dct_form.get("from_account", "")).strip()
            self.towards = str(dct_form.get("towards", "")).strip()
        else:
            raise ValueError

    def __str__(self):
        return f"Eur {self.amount} spend towards {self.towards} for {self.description} on {self.expense_date}"

    def validate(self, dct_form) -> bool:
        """
        Validates fields of the form
        """
        if (
            not dct_form.get("description")
            or not dct_form.get("amount")
            or not dct_form.get("date")
        ):
            raise ValueError(
                "Required Field Description, Amount or Expense Date not filled"
            )

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
            Expenses.query.order_by(Expenses.expense_date.desc(), Expenses.id.desc())
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
            db.session.query(func.sum(Expenses.amount))
            .filter(
                extract("year", Expenses.expense_date) == today.year,
                extract("month", Expenses.expense_date) == today.month,
            )
            .scalar()
        )

        # If no expenses exist, total will be None; return 0.0 instead
        return total if total is not None else 0.0

    except Exception as e:
        print(f"Error calculating monthly total: {e}")
        return 0.0


class ExpenseAnalytics:
    def __init__(self):
        pass

    def getLastCountRecords(limit=10) -> list:
        """
        List of Last 10 records
        """
        try:
            return list(
                Expenses.query.order_by(
                    Expenses.expense_date.desc(), Expenses.id.desc()
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
                db.session.query(func.sum(Expenses.amount))
                .filter(
                    extract("year", Expenses.expense_date) == today.year,
                    extract("month", Expenses.expense_date) == today.month,
                )
                .scalar()
            )

            # If no expenses exist, total will be None; return 0.0 instead
            return total if total is not None else 0.0

        except Exception as e:
            print(f"Error calculating monthly total: {e}")
            return 0.0

    def getExpensesBetweenDates(
        start_date=None, end_date=None, selected_category: str = None
    ) -> list:
        """
        List of expenses between `start_date` and `end_date`
        """
        if start_date is None:
            start_date = DateUtils.getStartOfCurrentMonth()

        if end_date is None:
            end_date = DateUtils.get_today_date()

        if selected_category is None:
            selected_category = ""

        try:
            query = Expenses.query

            if isinstance(start_date, str):
                if start_date is None:
                    start_date = datetime.strptime(
                        DateUtils.getStartOfCurrentMonth(), "%Y-%m-%d"
                    ).date()
                else:
                    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            if isinstance(end_date, str):
                if end_date is None:
                    end_date = datetime.strptime(
                        DateUtils.get_today_date(), "%Y-%m-%d"
                    ).date()
                else:
                    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

            if start_date:
                query = query.filter(Expenses.expense_date >= start_date)
            if end_date:
                query = query.filter(Expenses.expense_date <= end_date)

            if selected_category:
                query = query.filter(Expenses.category == selected_category)

            result = query.order_by(Expenses.expense_date.desc()).all()

            return result
        except Exception as e:
            print(e)
            raise Exception(e)

    def getExpensesPerCategoryForCurrentMonth(self) -> list:
        """
        Returns a list of tuples: (category, category_expense)
        summarized for the current month.
        """
        try:
            # 1. Get current month boundaries
            start_date = DateUtils.getStartOfCurrentMonth()
            end_date = DateUtils.get_now().date()

            # 2. Build the aggregate query
            results = (
                db.session.query(
                    Expenses.category,
                    func.sum(Expenses.amount).label("category_expense"),
                )
                .filter(Expenses.expense_date.between(start_date, end_date))
                .group_by(Expenses.category)
                .order_by(func.sum(Expenses.amount).desc())
                .all()
            )

            return results

        except Exception as e:
            db.session.rollback()
            print(f"Aggregation Error: {e}")
            raise Exception(f"Failed to fetch category expenses: {e}")
