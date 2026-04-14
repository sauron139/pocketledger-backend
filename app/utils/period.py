from datetime import date
from dateutil.relativedelta import relativedelta


def compute_period_bounds(start_date: date, period: str) -> tuple[date, date]:
    today = date.today()

    if period == "weekly":
        delta = relativedelta(weeks=1)
    elif period == "quarterly":
        delta = relativedelta(months=3)
    else:
        delta = relativedelta(months=1)

    period_start = start_date
    while period_start + delta <= today:
        period_start += delta

    return period_start, period_start + delta - relativedelta(days=1)


def compute_current_period(period: str) -> tuple[date, date]:
    today = date.today()

    if period == "weekly":
        delta = relativedelta(weeks=1)
    elif period == "quarterly":
        delta = relativedelta(months=3)
    else:
        delta = relativedelta(months=1)

    return today - delta + relativedelta(days=1), today


def compute_previous_period(period: str) -> tuple[date, date]:
    today = date.today()

    if period == "weekly":
        delta = relativedelta(weeks=1)
    elif period == "quarterly":
        delta = relativedelta(months=3)
    else:
        delta = relativedelta(months=1)

    period_end = today - delta
    period_start = period_end - delta + relativedelta(days=1)

    return period_start, period_end