"""Data-access layer: functions that read/write ORM models via a DB session.

Keeps SQL/ORM logic out of route handlers. Example: `app/crud/product.py` with
`get_product`, `list_products`, `create_product`, etc.
"""
