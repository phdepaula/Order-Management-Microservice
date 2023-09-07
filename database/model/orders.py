from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String

from database.database import Database

BASE = Database().BASE


class Orders(BASE):
    """Class to create the sales order table"""

    __tablename__ = "orders"

    orders_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(30))
    price = Column(Float)
    supplier = Column(String(100))
    category = Column(String(20))
    description = Column(String(500))
    sales_id = Column(Integer)
    quantity = Column(Integer)
    value = Column(Float)
    sale_date = Column(DateTime)
    zip_code = Column(String(15))
    country = Column(String(50))
    city = Column(String(50))
    state = Column(String(50))
    street = Column(String(50))
    neighborhood = Column(String(20))
    invoice_status = Column(String(10), default="Pending")

    def __init__(
        self,
        name: str,
        price: float,
        supplier: str,
        category: str,
        description: str,
        sales_id: int,
        quantity: int,
        value: float,
        sale_date: datetime,
        zip_code: str,
        country: str,
        city: str,
        state: str,
        street: str,
        neighborhood: str,
    ):
        self.name = name
        self.price = price
        self.supplier = supplier
        self.category = category
        self.description = description
        self.sales_id = sales_id
        self.quantity = quantity
        self.value = value
        self.sale_date = sale_date
        self.zip_code = zip_code
        self.country = country
        self.city = city
        self.state = state
        self.street = street
        self.neighborhood = neighborhood
