import time

def add(a, b):
    c = a + b  # <- set a breakpoint here
    return c

if __name__ == "__main__":
    x = add(2, 3)
    time.sleep(1)
    print("x =", x)