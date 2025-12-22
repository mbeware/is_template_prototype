import random
import tomllib
from typing import Any
import serviceUIconnectorModule 
import logging
import string


#from threading import Thread
from time import sleep
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('demoservice2')

class demo():
    def __init__(self):
        self.word=""
    def generate_random_letters(self):
        self.word = ''.join(random.choices(string.ascii_letters, k=10))
    
    def get_word(self):
        return self.word
    

serviceUIconnectorModule.demoapp = demo()

demoapp = serviceUIconnectorModule.demoapp



def load_config(config_path:str)->dict[str,Any]:
    try:
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        print(f"Error loading config file '{config_path}': {e}")
        exit(1)



def main():
    #global demoapp
    #start serviceUIconnector in a thread
    # load config and menu
    service_config = load_config("config/demoUIconfig2.toml")
    forms_config = load_config("config/demoUIforms2.toml")

    serviceUIconnectorApp = serviceUIconnectorModule.start_serviceUIconnector(service_config,forms_config)
    
    d={}
    d["word"]=serviceUIconnectorModule.demoapp.get_word
    serviceUIconnectorApp.registerInfo(d)
    quit = False




    while not quit :
        mainloop = random.randint(10,30)
        x=3 * mainloop
        print("main loop :",end="",flush=True)
        for _ in range(mainloop):
            sleep(float(float(random.randint(100,300))/float(100)))
            demoapp.generate_random_letters()
            print(f"last word generated is {demoapp.get_word()}", flush=True)
        
        print(f"Looped {mainloop} times. Now waiting for {x} seconds")
        sleep(x)
        print("Back to ", end="")

    serviceUIconnectorApp.quit()


if __name__ == "__main__":
    main()
