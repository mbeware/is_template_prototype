import tomllib
from typing import Any
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


def load_config(config_path:str)->dict[str,Any]:
    try:
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        print(f"Error loading config file '{config_path}': {e}")
        exit(1)

    

def main():
    global demoapp
    #start serviceUIconnector in a thread
    # load config and menu
    service_config = load_config("config/demoUIconfig.toml")
    forms_config = load_config("config/demoUIforms.toml")

    serviceUIconnectorApp = serviceUIconnector.start_serviceUIconnector(service_config,forms_config)
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
