import pandas as pd


def totalExpensePerCategory(dfExpense: pd.DataFrame, **args) -> pd.DataFrame:
    """
    Aggregates expenses for total expense per category based on fct_expense.

    Args:
        dfExpense (pd.DataFrame): The fct_expense dataframe.
        **args: Optional filters:
            - filter_category (list): List of parent_categories to include.
            - filter_start_date (str/date): Minimum expense_date.
            - filter_end_date (str/date): Maximum expense_date.
    """
    try:
        df = dfExpense.copy()

        # Apply Optional Filtering
        if args.get("filter_category"):
            df = df[df["parent_category"].isin(args["filter_category"])]

        if args.get("filter_start_date"):
            df = df[
                pd.to_datetime(df["expense_date"])
                >= pd.to_datetime(args["filter_start_date"])
            ]

        if args.get("filter_end_date"):
            df = df[
                pd.to_datetime(df["expense_date"])
                <= pd.to_datetime(args["filter_end_date"])
            ]

        # Aggregation Logic
        result = df.groupby("parent_category")["expend_amount"].sum().reset_index()
        return result.sort_values(by="expend_amount", ascending=False)
    except Exception as e:
        print(f"Error in totalExpensePerCategory: {e}")
        return pd.DataFrame()


def monthlyExpenseTrend(dfExpense: pd.DataFrame) -> pd.DataFrame:
    """KPI 2: Calculates total expenses grouped by month and year."""
    try:
        return (
            dfExpense.groupby(["year", "month", "month_year_marker"])["expend_amount"]
            .sum()
            .reset_index()
            .sort_values(["year", "month"])
        )
    except Exception as e:
        print(f"Error in monthlyExpenseTrend: {e}")
        return pd.DataFrame()


def dailyExpenseDistribution(dfExpense: pd.DataFrame) -> pd.DataFrame:
    """KPI 3: Analyzes average expenses based on the day of the week."""
    try:
        return (
            dfExpense.groupby(["num_day_of_week", "day_of_week"])["expend_amount"]
            .mean()
            .reset_index()
            .sort_values("num_day_of_week")
        )
    except Exception as e:
        print(f"Error in dailyExpenseDistribution: {e}")
        return pd.DataFrame()


def top10HighestExpenses(dfExpense: pd.DataFrame) -> pd.DataFrame:
    """KPI 4: Returns the top 10 individual expense entries by amount."""
    try:
        return dfExpense.nlargest(10, "expend_amount")[
            ["expense_date", "description", "parent_category", "expend_amount"]
        ]
    except Exception as e:
        print(f"Error in top10HighestExpenses: {e}")
        return pd.DataFrame()


def seasonalSpendingBreakdown(dfExpense: pd.DataFrame) -> pd.DataFrame:
    """KPI 5: Groups total expenses by the season of the year."""
    try:
        return (
            dfExpense.groupby("season")["expend_amount"]
            .sum()
            .reset_index()
            .sort_values(by="expend_amount", ascending=False)
        )
    except Exception as e:
        print(f"Error in seasonalSpendingBreakdown: {e}")
        return pd.DataFrame()


def accountSpendingSummary(dfExpense: pd.DataFrame) -> pd.DataFrame:
    """KPI 6: Breakdown of total spending per from_account_marker."""
    try:
        return (
            dfExpense.groupby("from_account_marker")["expend_amount"]
            .sum()
            .reset_index()
            .sort_values(by="expend_amount", ascending=False)
        )
    except Exception as e:
        print(f"Error in accountSpendingSummary: {e}")
        return pd.DataFrame()


def categoryTagInsights(dfExpense: pd.DataFrame) -> pd.DataFrame:
    """KPI 7: Analyzes spending patterns based on category tags."""
    try:
        return (
            dfExpense.groupby("category_tag")["expend_amount"]
            .sum()
            .reset_index()
            .sort_values(by="expend_amount", ascending=False)
        )
    except Exception as e:
        print(f"Error in categoryTagInsights: {e}")
        return pd.DataFrame()


def towardsCategoryAnalysis(dfExpense: pd.DataFrame) -> pd.DataFrame:
    """KPI 8: Summary of where the money is allocated (towards_category)."""
    try:
        return (
            dfExpense.groupby("towards_category")["expend_amount"]
            .sum()
            .reset_index()
            .sort_values(by="expend_amount", ascending=False)
        )
    except Exception as e:
        print(f"Error in towardsCategoryAnalysis: {e}")
        return pd.DataFrame()


def accountBalanceOverview(dfAccount: pd.DataFrame) -> pd.DataFrame:
    """KPI 9: Returns the current balance status per account from dim_account."""
    try:
        return dfAccount[["name", "type", "current_balance", "currency"]].sort_values(
            "current_balance", ascending=False
        )
    except Exception as e:
        print(f"Error in accountBalanceOverview: {e}")
        return pd.DataFrame()


def cumulativeSpendingTrend(dfExpense: pd.DataFrame) -> pd.DataFrame:
    """KPI 10: Calculates the cumulative spending over time ordered by date."""
    try:
        df = dfExpense.sort_values("expense_date")
        df["cumulative_amount"] = df["expend_amount"].cumsum()
        return df[["expense_date", "cumulative_amount"]]
    except Exception as e:
        print(f"Error in cumulativeSpendingTrend: {e}")
        return pd.DataFrame()
