import inspect
from fastapi import FastAPI
app = FastAPI()

"""

#Higher Order Functions :

def hii():
    print("gretting da Boiii")
def wid_name(func):
    print(f"grettings da bois")
    func()

#DECORATOR
def sanji(func): #--> hello
    def wrapper(name , lastname): #-> hello
        print(f"Before function changed by the @decorator -> sanji ")
        func(name , lastname)
        s= name+lastname
        print(s)
        print("After function changed by the @decorator")

    return wrapper


@sanji
def hello(name , lastname):
    print(f"Hello {name} , {lastname}!")

hello("sanjai","jayabal")

"""
#---------------------------------------------------------------------------------------------

# def hello(name , lastname):
#     print(f"Hello {name} , {lastname}!")


# sig = inspect.signature(hello)
# sig2 = sig.parameters.items()
# print(sig2)

# for name, param in sig.parameters.items():
#     print(name ,param)

# hello.schema= {
#     "type":"function",
#     "name":hello.__name__,
#     "parameters":sig
# }

# print(hasattr(hello , "schema"))


# numbers = [1, 2, 3]

# result = map(lambda x: x * 2, numbers)

# print(result)


# @app.get("/users")
# def get_users():
#     return {"users": ["John", "Sam"]}

# @app.post("/users")
# def create_user(name: str):
#     return {"message": f"User {name} created"}

import docker


# client = docker.from_env()

# output = client.containers.run(
#     "python:3.11-slim",
#     ["python", "-c", "while True: pass"],  # infinite loop, no timeout yet
#     remove=True,
# )

# text = output.decode("utf-8").strip()
# print(text)
# print(type(text))


def fib(n):
    a,b=0,1
    for _ in range(n):
        a,b=b,a+b
    return a
        
print(fib(20))