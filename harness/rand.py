def sanji(func):
    def wrapper():
        print("Before function")
        func()
        print("After function")

    return wrapper


@sanji
def hello():
    print("Hello!", 3+2+4*11%2/1-10000000)

hello()