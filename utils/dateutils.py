from datetime import datetime, date


class DateUtils:
    DATEFORMAT = "%Y-%m-%d"

    @classmethod
    def get_now(cls):
        """Helper to get fresh current time."""
        return datetime.now()

    @classmethod
    def get_today_date(cls):
        """Returns today date in DateFormat e.g. 2025-05-02"""
        return DateUtils.get_now().strftime(DateUtils.DATEFORMAT)

    @classmethod
    def getCurrentMonth(cls) -> int:
        """Returns current month as Integer (1-12)."""
        return cls.get_now().month

    @classmethod
    def getCurrentMonthWords(cls) -> str:
        """Returns current month name (e.g., 'May')."""
        return cls.get_now().strftime("%B")

    @classmethod
    def getCurrentYear(cls) -> int:
        """Returns current year as 4-digit Integer."""
        return cls.get_now().year

    @classmethod
    def getStartOfCurrentMonth(cls) -> str:
        """Returns the first day of the current month (e.g., '2026-05-01')."""
        today = cls.get_now()
        # Create a new date object forcing day to 1
        first_day = date(today.year, today.month, 1)
        return first_day.strftime(cls.DATEFORMAT)

    @classmethod
    def getDateTimeFromStingDate(cls, date_str):
        """
        Converts a string (YYYY-MM-DD) into a datetime object.
        If the input is already a datetime object, it returns it as is.
        """
        if not date_str:
            return None

        if isinstance(date_str, datetime):
            return date_str

        try:
            # Converts "2026-05-10" -> datetime.datetime(2026, 5, 10, 0, 0)
            return datetime.strptime(date_str, cls.DATEFORMAT)
        except ValueError as e:
            print(
                f"Date Conversion Error: {date_str} is not in format {cls.DATEFORMAT}"
            )
            return None
