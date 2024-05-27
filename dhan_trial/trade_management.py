from dhanhq import dhanhq

def place_order(dhan, tag, transaction_type, exchange_segment, product_type, order_type, validity, security_id,
                quantity, disclosed_quantity=0, price=0, trigger_price=0, after_market_order=False, amo_time='OPEN',
                bo_profit_value=0, bo_stop_loss_value=0, drv_expiry_date=None, drv_options_type=None,
                drv_strike_price=None):
    try:
        order = dhan.place_order(
            tag=tag,
            transaction_type=transaction_type,
            exchange_segment=exchange_segment,
            product_type=product_type,
            order_type=order_type,
            validity=validity,
            security_id=security_id,
            quantity=quantity,
            disclosed_quantity=disclosed_quantity,
            price=price,
            trigger_price=trigger_price,
            after_market_order=after_market_order,
            amo_time=amo_time,
            bo_profit_value=bo_profit_value,
            bo_stop_loss_Value=bo_stop_loss_value,
            drv_expiry_date=drv_expiry_date,
            drv_options_type=drv_options_type,
            drv_strike_price=drv_strike_price
        )
        print("Order placed successfully.")
        return order
    except Exception as e:
        print(f"An error occurred while placing the order: {e}")
        return None


def modify_order(dhan, order_id, **kwargs):
    try:
        order = dhan.modify_order(order_id=order_id, **kwargs)
        print("Order modified successfully.")
        return order
    except Exception as e:
        print(f"An error occurred while modifying the order: {e}")
        return None


def cancel_order(dhan, order_id):
    try:
        result = dhan.cancel_order(order_id=order_id)
        print("Order canceled successfully.")
        return result
    except Exception as e:
        print(f"An error occurred while canceling the order: {e}")
        return None


def place_slice_order(dhan, **kwargs):
    try:
        order = dhan.place_slice_order(**kwargs)
        print("Slice order placed successfully.")
        return order
    except Exception as e:
        print(f"An error occurred while placing the slice order: {e}")
        return None


def get_order_list(dhan):
    try:
        orders = dhan.get_order_list()
        print("Retrieved order list successfully.")
        return orders
    except Exception as e:
        print(f"An error occurred while retrieving the order list: {e}")
        return None


def get_order_by_id(dhan, order_id):
    try:
        order = dhan.get_order_by_id(order_id=order_id)
        print("Retrieved order by ID successfully.")
        return order
    except Exception as e:
        print(f"An error occurred while retrieving the order by ID: {e}")
        return None


def get_order_by_corelationID(dhan, corelation_id):
    try:
        order = dhan.get_order_by_corelationID(corelation_id=corelation_id)
        print("Retrieved order by correlation ID successfully.")
        return order
    except Exception as e:
        print(f"An error occurred while retrieving the order by correlation ID: {e}")
        return None


def get_trade_book(dhan):
    try:
        trades = dhan.get_trade_book()
        print("Retrieved trade book successfully.")
        return trades
    except Exception as e:
        print(f"An error occurred while retrieving the trade book: {e}")
        return None


def get_trade_by_order_id(dhan, order_id):
    try:
        trade = dhan.get_trade_book(order_id=order_id)
        print("Retrieved trade by order ID successfully.")
        return trade
    except Exception as e:
        print(f"An error occurred while retrieving the trade by order ID: {e}")
        return None
