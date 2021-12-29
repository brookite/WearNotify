def raw_input():
    try:
        return input(">> ")
    except EOFError:
        pass
