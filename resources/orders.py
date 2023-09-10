import requests
from flask_openapi3 import Tag

from app import app, database
from database.model.orders import Orders
from schemas.orders import (
    MessageOrderSchema,
    OrderCloseSchema,
    SingleMessageSchema,
    format_add_order_response,
)

TAG_ORDERS = Tag(
    name="Orders",
    description="Routes for controlling sales orders."
)


@app.get(
    "/get_sales_order",
    tags=[TAG_ORDERS],
    responses={
        "200": MessageOrderSchema,
        "400": SingleMessageSchema,
    },
)
def get_sales_order():
    """Get sales orders that are open via the online store api."""
    try:
        get_sales_url = "http://online-store-microservice:5000/get_sales"
        response_get_sales = requests.get(get_sales_url)
        response_sales_data = response_get_sales.json()

        if response_get_sales.status_code == 400:
            raise Exception(
                response_sales_data["message"].replace("Error: ", "")
            )

        sales_data = response_sales_data.get("sales", [])

        address_columns = {
            "city": "localidade",
            "state": "uf",
            "street": "logradouro",
            "neighborhood": "bairro",
        }
        updated_sales_data = []

        for sale in sales_data:
            empty_address_columns = [
                key for key in address_columns
                if len(sale.get(key, "").strip()) == 0
            ]

            if len(empty_address_columns) > 0 and sale["country"] in [
                "Brazil",
                "Brasil",
            ]:
                get_viacep_url = "http://127.0.0.1:5001/get_viacep/?zip_code="
                zip_code = sale.get("zip_code", "")
                response_get_viacep = requests.get(
                    f"{get_viacep_url}{zip_code}"
                )
                data_viacep = response_get_viacep.json().get("data", {})

                if (
                    response_get_viacep.status_code == 200
                    and len(data_viacep) > 0
                ):
                    for empty_column in empty_address_columns:
                        sale[empty_column] = (
                            data_viacep[address_columns[empty_column]]
                        )

            updated_sales_data.append(sale)

        return {"message": "Success", "sales_data": updated_sales_data}, 200
    except Exception as error:
        return {"message": f"Error: {error}"}, 400


@app.post(
    "/add_order",
    tags=[TAG_ORDERS],
    responses={
        "200": MessageOrderSchema,
        "400": SingleMessageSchema,
    },
)
def add_order():
    """Adds all updated sales order information."""
    try:
        get_order_url = "http://127.0.0.1:5001/get_sales_order"
        response_get_order = requests.get(get_order_url)
        response_order_data = response_get_order.json()

        if response_get_order.status_code == 400:
            raise Exception(
                response_order_data["message"].replace("Error: ", "")
            )

        orders_data = response_order_data.get("sales_data", {})
        added_orders = []

        for order in orders_data:
            new_order = Orders(
                name=order.get("name", ""),
                price=order.get("price", ""),
                supplier=order.get("supplier", ""),
                category=order.get("category", ""),
                description=order.get("description", ""),
                sales_id=order.get("sales_id", ""),
                quantity=order.get("quantity", ""),
                value=order.get("value", ""),
                sale_date=order.get("sale_date", ""),
                zip_code=order.get("zip_code", ""),
                country=order.get("country", ""),
                city=order.get("city", ""),
                state=order.get("state", ""),
                street=order.get("street", ""),
                neighborhood=order.get("neighborhood", ""),
            )
            formatted_response = format_add_order_response(new_order)
            added_orders.append(formatted_response)
            database.insert_data_table(new_order)

            close_sale_url = "http://online-store-microservice:5000/close_sale"
            sales_id = {"sales_id": int(order["sales_id"])}
            response_close_sale = requests.put(close_sale_url, data=sales_id)
            close_sale_data = response_close_sale.json()

            if response_close_sale.status_code == 400:
                raise Exception(
                    close_sale_data["message"].replace("Error: ", "")
                )

        return {"message": "Added Orders", "orders": added_orders}, 200
    except Exception as error:
        return {"message": f"Error: {error}"}, 400


@app.get(
    "/get_pending_invoices",
    tags=[TAG_ORDERS],
    responses={
        "200": MessageOrderSchema,
        "400": SingleMessageSchema,
    },
)
def get_pending_invoices():
    """Get orders with pending invoice status."""
    try:
        status_pending = "Pending"
        pending_orders = database.select_data_table(
            table=Orders,
            filter_select={Orders.invoice_status: status_pending},
        )

        if len(pending_orders) == 0:
            raise Exception("There are no pending orders")

        content = []

        for order in pending_orders:
            order_data = {}

            order_id = order.order_id
            order_data["order_id"] = order_id

            other_order_data = format_add_order_response(order)
            order_data.update(other_order_data)

            content.append(order_data)

        return {"message": " There are pending orders", "orders": content}, 200
    except Exception as error:
        return {"message": f"Error: {error}"}, 400


@app.put(
    "/complete_order",
    tags=[TAG_ORDERS],
    responses={
        "200": MessageOrderSchema,
        "400": SingleMessageSchema,
    },
)
def complete_order(form: OrderCloseSchema):
    """Closes a order from the orders table."""
    order_id = form.order_id

    try:
        registered_order = database.select_value_table_parameter(
            column=Orders.order_id, filter_select={Orders.order_id: order_id}
        )

        if not registered_order:
            raise Exception(f"The order {order_id} does not exist")

        invoice_status = database.select_value_table_parameter(
            column=Orders.invoice_status,
            filter_select={Orders.order_id: order_id}
        )

        if invoice_status == "Completed":
            raise Exception(f"The order {order_id} is already completed")

        new_invoice_status = "Completed"
        database.update_data_table(
            table=Orders,
            filter_update={Orders.order_id: order_id},
            new_data={Orders.invoice_status: new_invoice_status},
        )

        return {"message": f"Order {order_id} completed successfully"}, 200
    except Exception as error:
        return {"message": f"Error: {error}"}, 400
