import datetime
import unittest

from src import export, invoices

D = datetime.date


def invoice(number, issued, paid=False, lines=()):
    return {"number": number, "issued": issued, "paid": paid, "lines": list(lines)}


class Totals(unittest.TestCase):
    def test_line_amount(self):
        self.assertEqual(invoices.line_amount({"quantity": 3, "unit_price_cents": 250}), 750)

    def test_total(self):
        inv = invoice(17, D(2026, 10, 1), lines=[{"quantity": 3, "unit_price_cents": 250},
                                                 {"quantity": 1, "unit_price_cents": 1200}])
        self.assertEqual(invoices.total(inv), 1950)


class Reminders(unittest.TestCase):
    def test_thirty_days(self):
        self.assertEqual(invoices.reminders([invoice(17, D(2026, 10, 1))], D(2026, 10, 31)), [17])

    def test_paid(self):
        self.assertEqual(invoices.reminders([invoice(18, D(2026, 9, 1), paid=True)], D(2026, 10, 31)), [])


class Export(unittest.TestCase):
    def test_one_invoice(self):
        inv = invoice(17, D(2026, 10, 1), lines=[{"quantity": 1, "unit_price_cents": 1950}])
        self.assertEqual(export.export_csv([inv]), "number,date,total\n17,2026-10-01,1950\n")
