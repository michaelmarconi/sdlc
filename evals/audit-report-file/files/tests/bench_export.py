"""Prints the time taken to export 10,000 invoices."""
import datetime
import time

from src import export

rows = [{"number": n, "issued": datetime.date(2026, 1, 1), "paid": False,
         "lines": [{"quantity": 1, "unit_price_cents": 100}]} for n in range(10000)]
start = time.perf_counter()
export.export_csv(rows)
print(f"{time.perf_counter() - start:.3f} seconds")
