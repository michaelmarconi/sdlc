"""Export invoices as CSV for the accountant."""

import csv
import io

from src.invoices import total


def export_csv(invoices):
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["number", "date", "total"])
    for inv in invoices:
        writer.writerow([inv["number"], inv["issued"].isoformat(), total(inv)])
    return out.getvalue()
