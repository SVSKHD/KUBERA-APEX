from connect import dhan  # Importing the Dhan client


# Function to place an order
def place_order(symbol, quantity, order_type, price=None):
    try:
        order_params = {
            "symbol": symbol,
            "quantity": quantity,
            "order_type": order_type,
            "exchange_segment": "NSE_EQ",
            "instrument_type": "EQUITY",
            "order_source": "API"
        }

        if order_type in ["LIMIT", "STOP_LOSS"]:
            if price is None:
                raise ValueError("Price must be specified for LIMIT or STOP_LOSS orders")
            order_params["price"] = price

        order_response = dhan.place_order(order_params)
        if order_response['status'] == 'success':
            print(f"Order placed successfully: {order_response['order_id']}")
            return order_response['order_id']
        else:
            print(f"Failed to place order: {order_response['message']}")
            return None
    except Exception as e:
        print(f"Error placing order: {e}")
        return None


# Function to get order details
def get_order(order_id):
    try:
        order_details = dhan.get_order(order_id)
        if order_details['status'] == 'success':
            return order_details['order']
        else:
            print(f"Failed to get order details: {order_details['message']}")
            return None
    except Exception as e:
        print(f"Error getting order details: {e}")
        return None


# Function to modify an existing order
def modify_order(order_id, quantity=None, price=None):
    try:
        modify_params = {"order_id": order_id}

        if quantity is not None:
            modify_params["quantity"] = quantity

        if price is not None:
            modify_params["price"] = price

        modify_response = dhan.modify_order(modify_params)
        if modify_response['status'] == 'success':
            print(f"Order modified successfully: {modify_response['order_id']}")
            return modify_response['order_id']
        else:
            print(f"Failed to modify order: {modify_response['message']}")
            return None
    except Exception as e:
        print(f"Error modifying order: {e}")
        return None


# Example usage
if __name__ == "__main__":
    symbol = "TCS"
    quantity = 10
    order_type = "MARKET"  # Other types: LIMIT, STOP_LOSS

    # Place a new order
    order_id = place_order(symbol, quantity, order_type)
    if order_id:
        # Get the order details
        order_details = get_order(order_id)
        if order_details:
            print(f"Order details: {order_details}")

        # Modify the order
        modified_order_id = modify_order(order_id, quantity=20, price=4000)
        if modified_order_id:
            print(f"Order modified with new ID: {modified_order_id}")
