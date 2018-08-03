def isFloat(num):
    """
    Returns True if input is a number, otherwise False.
    """
    try:
        float(num)
        return True
    except (TypeError, ValueError):
        return False
