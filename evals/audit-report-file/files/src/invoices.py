"""Invoice totals and reminders. Every amount is a whole number of cents."""


def line_amount(line):
    return line["quantity"] * line["unit_price_cents"]


def total(invoice):
    return sum(line_amount(line) for line in invoice["lines"])


def total_with_vat(invoice):
    return total(invoice) * 1.2


def reminders(invoices, today):
    """Numbers of unpaid invoices issued 30 days or more before today."""
    return [inv["number"] for inv in invoices
            if not inv["paid"] and (today - inv["issued"]).days >= 30]
