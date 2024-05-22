def calculate_lot_size(account_balance, risk_percentage, stop_loss_pips, symbol):
    risk_amount = account_balance * (risk_percentage / 100)
    # Fetching symbol info to get the tick value, assuming similar to MT5
    symbol_info = dhan.get_symbol_info(symbol)
    tick_value = symbol_info['tick_size']
    lot_size = risk_amount / (stop_loss_pips * tick_value)
    return lot_size

def place_order_dhan(dhan, symbol, action, current_price, stop_loss, take_profit, lot_size):
    order_type = 'BUY' if action == 'BUY' else 'SELL'
    dhan.place_order(
        symbol=symbol,
        transaction_type=order_type,
        quantity=lot_size,
        price=current_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        order_type="MARKET",
        product_type="INTRADAY"
    )

def close_order_dhan(dhan, order_id):
    dhan.cancel_order(order_id)
