def list_same_elements(l1: list, l2: list) -> bool:
    """
    Checks if two lists are equal (order doesn't matter)
    :param l1: The first list
    :param l2: The second list
    :return: True if the lists are equal, false otherwise
    """
    l1 = l1.copy()
    l2 = l2.copy()

    if len(l1) != len(l2):
        return False

    for i in l1:
        found_match = False
        for j in l2:
            if i == j:
                l2.remove(j)
                found_match = True
                break
        if not found_match:
            return False

    return True
