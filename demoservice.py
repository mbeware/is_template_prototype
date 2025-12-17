import serviceUIconnector
#from threading import Thread
from time import sleep


class demo():
    def __init__(self):
        self.i=0

    def inc_i(self):
        self.i = self.i + 1

    def get_i(self):
        return self.i

demoapp = demo()

def main():
    global demoapp
    #start serviceUIconnector in a thread
    serviceUIconnectorApp = serviceUIconnector.start_serviceUIconnector("config/connector.toml")
    quit = False
    

    while not quit :
        for _ in range(10):
            print(f"Loop {demoapp.get_i()} done")
            sleep(1)
            demoapp.inc_i()
        print("waiting a bit")
        sleep(5)
    serviceUIconnectorApp.quit()


if __name__ == "__main__":
    main()
