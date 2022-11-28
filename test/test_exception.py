def create_valueerror(n):
    if n < 10:
        raise ValueError(f"N要大於10, n={n}")
    else:
        print(n)

def create_typeerror():
    raise TypeError("TYERROR")

def test_exception():
    create_valueerror(3)

if __name__ == '__main__':
    test_exception()