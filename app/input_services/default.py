def raw_input(ctx):
    try:
        return input(">> ")
    except EOFError:
        pass
