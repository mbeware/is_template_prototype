import random
import tomli as tomllib
from typing import Any
import serviceUIconnectorModule 
import logging



#from threading import Thread
from time import sleep
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('demoservice')

class demo():
    def __init__(self):
        self.i=0


    def inc_i(self):
        self.i += 1

    def get_i(self):
        return self.i

serviceUIconnectorModule.demoapp = demo()

demoapp = serviceUIconnectorModule.demoapp



def load_config(config_path:str)->dict[str,Any]:
    try:
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        print(f"Error loading config file '{config_path}': {e}")
        exit(1)

def getloops():
    return demoapp.get_i()

def main():
    #global demoapp
    #start serviceUIconnector in a thread
    # load config and menu
    service_config = load_config("config/demoUIconfig.toml")
    forms_config = load_config("config/demoUIforms.toml")

    serviceUIconnectorApp = serviceUIconnectorModule.start_serviceUIconnector(service_config,forms_config)
    
    d={}
    d["nbLoops"]=serviceUIconnectorModule.demoapp.get_i
    serviceUIconnectorApp.registerInfo(d)
    quit = False




    while not quit :
        mainloop = random.randint(10,30)
        x=3 * mainloop
        print("main loop :",end="",flush=True)
        for _ in range(mainloop):
            sleep(1)
            demoapp.inc_i()
            print(".", end="", flush=True)
        print("")
        print(f"Looped {mainloop} times. Since demo started, looped for{demoapp.get_i()} times. Now waiting for {x} seconds")
        sleep(x)
        print("Back to ", end="")

    serviceUIconnectorApp.quit()


if __name__ == "__main__":
    main()
