from pydantic import BaseModel

from database.model.orders import Orders


class MessageOrderSchema(BaseModel):
    """Defines how the API response should be \
    like for a successful sales order."""

    message: str
    sales_data: list


class SingleMessageSchema(BaseModel):
    """
    Defines how the API response should be \
    when you want to send just one message.
    """

    message: str


class OrderCloseSchema(BaseModel):
    """
    Defines how a order id must be passed to be closed.
    """

    order_id: int


def format_add_order_response(order: Orders) -> dict:
    """
    Format the API response for a added order.
    """
    response = {
        "name": order.name,
        "price": order.price,
        "supplier": order.supplier,
        "category": order.category,
        "description": order.description,
        "sales_id": order.sales_id,
        "quantity": order.quantity,
        "value": order.value,
        "sale_date": order.sale_date,
        "zip_code": order.zip_code,
        "country": order.country,
        "city": order.city,
        "state": order.state,
        "street": order.street,
        "neighborhood": order.neighborhood,
    }

    return response
