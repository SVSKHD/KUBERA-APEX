from dhanhq import dhanhq


class TradeManagement:
    def __init__(self, client_id, access_token):
        self.dhan = dhanhq(client_id, access_token)

    def place_order(self, symbol, quantity, order_type, price=None):
        try:
            order_data = {
                'symbol': symbol,
                'quantity': quantity,
                'order_type': order_type,  # 'buy' or 'sell'
                'price': price  # Only for limit orders
            }
            response = self.dhan.place_order(order_data)
            print(f"Order placed: {response}")
            return response
        except Exception as e:
            print(f"Failed to place order: {e}")
            return None

    def modify_order(self, order_id, quantity=None, price=None):
        try:
            order_data = {
                'order_id': order_id,
                'quantity': quantity,
                'price': price
            }
            response = self.dhan.modify_order(order_data)
            print(f"Order modified: {response}")
            return response
        except Exception as e:
            print(f"Failed to modify order: {e}")
            return None

    def slice_order(self, order_id, slice_size):
        try:
            response = self.dhan.slice_order(order_id, slice_size)
            print(f"Order sliced: {response}")
            return response
        except Exception as e:
            print(f"Failed to slice order: {e}")
            return None
