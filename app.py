from sqlite3 import IntegrityError
import os
import traceback
from flask import (
    Flask,
    render_template,
    request,
    url_for,
    make_response,
    flash,
    redirect,
)
from models import (
    db,
    Database,
    Expenses,
    getLastCountRecords,
    get_current_month_total,
    ExpenseAnalytics,
)
from utils.dateutils import DateUtils

basedir = os.path.abspath(os.path.dirname(__file__))

# WebApp Create
app = Flask(__name__)

# WebApp Config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///expenses.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "my-secret-key"

# DB Create
db.init_app(app)
db_manager = Database()

# Global Vars
DATE_FORMAT = "%Y-%m-%d"
CATEGORIES = sorted(
    [
        "Transportation",
        "Grocery",
        "Food",
        "Cigga",
        "Green",
        "Mobile",
        "Relocation",
        "Personal",
        "Entertainment",
        "Home",
    ]
)
ACCOUNT_TYPES = ["N26", "Wise", "Deutsche Bank", "Cash"]

with app.app_context():
    db.create_all()
    print(f"Database created at: {app.config['SQLALCHEMY_DATABASE_URI']}")


@app.route("/")
def index():

    start_date = (request.args.get("filter_start_date", "")).strip()
    end_date = (request.args.get("filter_end_date", "")).strip()
    selectedCategory = (request.args.get("categories", "")).strip()

    start_date = DateUtils.getDateTimeFromStingDate(start_date)
    end_date = DateUtils.getDateTimeFromStingDate(end_date)

    # basic validation
    if not start_date or not end_date or end_date < start_date:
        flash("End date cannot be before start date", "error")
        start_date = DateUtils.getStartOfCurrentMonth()
        end_date = DateUtils.get_today_date()
        # retrives records from start of month to current date
    lstRecordsBetweenDates = ExpenseAnalytics.getExpensesBetweenDates(
        start_date=start_date, end_date=end_date, selected_category=selectedCategory
    )
    totalDefaultFilterView = float(
        round(sum([e.amount for e in lstRecordsBetweenDates]), 2)
    )

    return render_template(
        "index.html",
        # expenses=getLastCountRecords(),
        expenses=lstRecordsBetweenDates,
        categories=CATEGORIES,
        accountTypes=ACCOUNT_TYPES,
        totalExpenseCurrentMonth=get_current_month_total(),
        expenseReportBetweenDates=lstRecordsBetweenDates,
        filter_start_date=start_date,
        filter_end_date=end_date,
        today=DateUtils.get_today_date(),
        lstDefaultFilterView=lstRecordsBetweenDates,
        totalDefaultFilterView=totalDefaultFilterView,
    )


@app.route("/add", methods=["POST"])
def add():
    # Get Fields
    form_data = dict(request.form)

    # Create Record
    expense_row = Expenses(form_data)

    # Add Row
    try:
        db_manager.insert(expense_row)
        flash("Expense Row Added", "success")
        return redirect(url_for("index"))
    except IntegrityError as e:
        flash(f"Database Error: Required data missing or invalid.\n{e}", "danger")
        return redirect(url_for("index"))
    except Exception as ex:
        flash("Error adding expense to DB", "error")
        return redirect(url_for("index"))


@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete(expense_id):
    try:
        status = db_manager.delete(Expenses, expense_id)
        if not status:
            raise Exception
        flash(f"Record ID: {expense_id} is deleted", "Success")
        return redirect(url_for("index"))
    except Exception as e:
        flash("Exception in deleting Expense", "Error")
        raise Exception(f"Exception deleting record\n{e}")


if __name__ == "__main__":
    # Run App
    app.run(host="0.0.0.0", port=5001, debug=True)
