def isNum(num):
    """
    @brief:     Check if the num is a float
    @param:     num - value to check if is a float
    @return:    Float on success, else None
    """
    try:
        return float(num)
    except ValueError:
        return None

def coinNormalization(order):
    """
    @brief:     Add 'USDT' to the coin only if coin is not USDT
    @param:     order - new order with the value of the 'Coin'
    @return:    Normalized coin on the order
    """
    if order['Coin'] != 'USDT':
        order['Coin'] += 'USDT'
    return order

def amountValidation(order):
    """
    @brief:     Check if the value for 'Amount' is a float
    @param:     order - new order with the value of the 'Amount'
    @return:    Validated amount on success, else error message
    """
    num = isNum(order['Amount'])
    if num:
        order['Amount'] = num
        return order, None
    else:
        return None, 'Numbers only for amount'

def amountNormalization(order):
    """
    @brief:     Set the amount to be a negative if 'Direction'
                is set to be 'SELL'
    @param:     order - new order with the value of the 'Amount'
    @return:    Normalized amount on the order
    """
    if order['Direction'] == 'SELL':
        order['Amount'] = -1 * abs(order['Amount'])
    order['Amount'] = '{:,}'.format(order['Amount'])

    return order

def priceValidation(order):
    """
    @brief:     Check if the value for 'Price' is a float
    @param:     order - new order with the value of the 'Price'
    @return:    Validated price on success, else error message
    """
    num = isNum(order['Price'])
    if num:
        order['Price'] = num
        return order, None
    else:
        return None, 'Numbers only for price'

def priceNormalization(order):
    """
    @brief:     Add '$' and comma to the price to make it look pretty
    @param:     order - new order with the value of the 'Price'
    @return:    Normalized price on the order.
    """
    order['Price'] = '${:,}'.format(order['Price'])
    return order

def validateNormalizeOrder(order):
    """
    @brief:     Go through the values from new submitted order and
                check if values are valid. If successful, normalize
                data. Else, report the issue.
    @return:    Normalized order on success, else error message.
    """
    order = coinNormalization(order)

    order, msg = amountValidation(order)
    if order is None:
        return None, msg
    order = amountNormalization(order)

    order, msg = priceValidation(order)
    if order is None:
        return None, msg
    order = priceNormalization(order)

    return order, None
