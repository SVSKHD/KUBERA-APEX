

# singleStament


# get orders


# calculate profit


# get capital


#place order
def place_order(self, symbol, quantity, order_type, price=None, order_side='buy', product='CNC', validity='DAY',
                order_variety='LIMIT'):
    order_data = {
        "symbol": symbol,
        "quantity": quantity,
        "order_type": order_type,
        "price": price,
        "order_side": order_side,
        "product": product,
        "validity": validity,
        "order_variety": order_variety
    }

    response = self.client.place_order(**order_data)

    return response
