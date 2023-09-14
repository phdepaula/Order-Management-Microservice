import requests
from flask_openapi3 import Tag

from app import app, database, log
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
    log.add_message("Get_sales_order route accessed")

    try:
        log.add_message("Accessing Online Store container to get sales")

        get_sales_url = "http://online-store-microservice:5000/get_sales"
        response_get_sales = requests.get(get_sales_url)
        response_sales_data = response_get_sales.json()

        if response_get_sales.status_code == 400:
            raise Exception(
                response_sales_data["message"].replace("Error: ", "")
            )

        log.add_message("Sales achieved")

        sales_data = response_sales_data.get("sales", [])

        address_columns = {
            "city": "localidade",
            "state": "uf",
            "street": "logradouro",
            "neighborhood": "bairro",
        }

        log.add_message("Checking empty address fields")

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
                log.add_message(f"Sale {sale['sales_id']} is incomplete")
                log.add_message(
                    f'Empty colums: {", ".join(empty_address_columns)}'
                )
                log.add_message("")

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
                        new_data = data_viacep[address_columns[empty_column]]
                        sale[empty_column] = new_data

                        log.add_message(
                            f"{empty_column} updated with {new_data}"
                        )

            updated_sales_data.append(sale)

        return_data = {"message": "Success", "sales_data": updated_sales_data}

        log.add_message(f"Get_sales_order response: {return_data}")
        log.add_message("Get_sales_order status: 200")
        log.add_message("")

        return return_data, 200
    except Exception as error:
        return_data = {"message": f"Error: {error}"}

        log.add_message(f"Get_sales_order: {return_data}")
        log.add_message("Get_sales_order: 400")
        log.add_message("")

        return return_data, 400


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
    log.add_message("Add_order route accessed")

    try:
        log.add_message("")

        get_order_url = "http://127.0.0.1:5001/get_sales_order"
        response_get_order = requests.get(get_order_url)
        response_order_data = response_get_order.json()

        if response_get_order.status_code == 400:
            raise Exception(
                response_order_data["message"].replace("Error: ", "")
            )

        orders_data = response_order_data.get("sales_data", {})
        added_orders = []

        log.add_message("Adding orders")

        for order in orders_data:
            log.add_message("")
            log.add_message(f"Sale {order['sales_id']}")

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

            log.add_message("Order added")
            log.add_message("Accessing Online Store container to close sale")

            close_sale_url = "http://online-store-microservice:5000/close_sale"
            sales_id = {"sales_id": int(order["sales_id"])}
            response_close_sale = requests.put(close_sale_url, data=sales_id)
            close_sale_data = response_close_sale.json()

            if response_close_sale.status_code == 400:
                raise Exception(
                    close_sale_data["message"].replace("Error: ", "")
                )

            log.add_message("Closed sale")

        return_data = {"message": "Added Orders", "orders": added_orders}

        log.add_message(f"Add_order response: {return_data}")
        log.add_message("Add_order status: 200")
        log.add_message("")

        return return_data, 200
    except Exception as error:
        return_data = {"message": f"Error: {error}"}

        log.add_message(f"Add_order response: {return_data}")
        log.add_message("Add_order status: 400")
        log.add_message("")

        return return_data, 400


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
    log.add_message("Get_pending_invoices route accessed")

    try:
        log.add_message("Checking if there are pending orders")

        status_pending = "Pending"
        pending_orders = database.select_data_table(
            table=Orders,
            filter_select={Orders.invoice_status: status_pending},
        )

        if len(pending_orders) == 0:
            raise Exception("There are no pending orders")

        log.add_message(f"There are {len(pending_orders)} pending orders")

        content = []

        for order in pending_orders:
            order_data = {}

            order_id = order.order_id
            order_data["order_id"] = order_id

            other_order_data = format_add_order_response(order)
            order_data.update(other_order_data)

            content.append(order_data)

        return_data = {
            "message": "There are pending orders",
            "orders": content
        }

        log.add_message(f"Get_pending_invoices response: {return_data}")
        log.add_message("Get_pending_invoices status: 200")
        log.add_message("")

        return return_data, 200
    except Exception as error:
        return_data = {"message": f"Error: {error}"}

        log.add_message(f"Get_pending_invoices response: {return_data}")
        log.add_message("Get_pending_invoices status: 400")
        log.add_message("")

        return return_data, 400


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
    log.add_message("Complete_order route accessed")

    order_id = form.order_id

    try:
        registered_order = database.select_value_table_parameter(
            column=Orders.order_id, filter_select={Orders.order_id: order_id}
        )

        log.add_message(f"Checking if order {order_id} exists")

        if not registered_order:
            raise Exception(f"The order {order_id} does not exist")

        log.add_message("The order exists")

        invoice_status = database.select_value_table_parameter(
            column=Orders.invoice_status,
            filter_select={Orders.order_id: order_id}
        )

        log.add_message(f"Checking if order {order_id} is completed")

        if invoice_status == "Completed":
            raise Exception(f"The order {order_id} is already completed")

        log.add_message("The order is pending and will be finalized")

        new_invoice_status = "Completed"
        database.update_data_table(
            table=Orders,
            filter_update={Orders.order_id: order_id},
            new_data={Orders.invoice_status: new_invoice_status},
        )

        return_data = {"message": f"Order {order_id} completed successfully"}

        log.add_message(f"Complete_order response: {return_data}")
        log.add_message("Complete_order status: 200")
        log.add_message("")

        return return_data, 200
    except Exception as error:
        return_data = {"message": f"Error: {error}"}

        log.add_message(f"Complete_order response: {return_data}")
        log.add_message("Complete_order status: 400")
        log.add_message("")

        return return_data, 400
