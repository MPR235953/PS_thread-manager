import threading

def hello():
    print("Hello World!")

if __name__ == '__main__':
    th = threading.Thread(target=hello)
    th.start()
    th.join()
