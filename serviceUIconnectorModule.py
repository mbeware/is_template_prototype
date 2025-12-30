import serviceUIinterface as sUIi
from serviceUIlogging import webUIlogger

import json
from typing import Any
import tomli as tomllib 
import threading
import time
import os
import tempfile

import copy 


SERVICEUICONNECTION_CONFIG_PATH = "config/serviceUIconnector.toml"


class serviceUIconnector(threading.Thread):

    def old_register_service(self,service_name:str|None=None):
        
        # Register the service in the serviceUIwebserver FIFO.
        # get the fifo path from the config file
        if not service_name:
            service_name = self.config["service_name"]

        webServerFifoPath = self.config["register_fifo_path"]  
        # message format : "{service_name:"<service_name>", 
        #           action:"Register",
        #                   connectorFifoPath:"<webServerFifoPath>"}

        # write message to webServerFifoPath
        print(f"want to register [Service '{service_name}' with connector fifo at '{self.serviceFifo_path}'")

        with open(webServerFifoPath, "w") as f:
            f.write(f'{{"service_name":"{service_name}","action":"Register","connectorFifoPath":"{self.serviceFifo_path}"}}')
        print(f"[Service '{service_name}' registered with connector fifo at '{self.serviceFifo_path}'")

    def register_service(self,service_name:str|None=None):
        
        # Register the service in the serviceUIwebserver FIFO.
        # get the fifo path from the config file
        if not service_name:
            service_name = self.config["service_name"]

        webServerFifoPath = self.config["register_fifo_path"]  
        
        registerMessage=sUIi.RegisterMessageToUI(service_name,
                                                 sUIi.ActionType.Register,
                                                 webServerFifoPath)
        # write message to webServerFifoPath
        webUIlogger.info(f"want to register [Service '{service_name}' with connector fifo at '{self.serviceFifo_path}'")
        
        with open(webServerFifoPath, "w") as f:
            print(f"{registerMessage.to_json()}")
            f.write(registerMessage.to_json())
        print(f"[Service '{service_name}' registered with connector fifo at '{self.serviceFifo_path}'")


    def merge_configs(self,serviceConfig:dict[str,Any],formsConfig:dict[str,Any])->dict[str,Any]:
        # Load the configuration from a file or other source.
        config = {}
        with open(SERVICEUICONNECTION_CONFIG_PATH, "rb") as f:
            config = tomllib.load(f)
        
        # merge the 2 configs from the service 
        config.update(formsConfig)
        config.update(serviceConfig)
        return config

    def listen_to_connector(self):
        # start a thread to listen to the connector fifo
        with open(self.serviceFifo_path, "r") as f:
            while not self.quitRequested:
                # Read message from fifo (this is blocking)
                message = f.read()
                if message != "":
                    #print(f"[FR] Message reçu: {message}")
                    # Process message
                    self.handle_messages(message)
                time.sleep(0.1)
                
    def handle_messages(self, message):
        
        message_dict = json.loads(message)
        sourceform = message_dict["formid"]
        sourcewidget_type = message_dict["widget_type"]

        data = ""
        if sourcewidget_type == "menu" :
            data = message_dict["choice"]
        
    
        newformname = self.config["navigation"][sourceform][data]
        newform = copy.deepcopy(self.config[newformname])

        form:dict[str,Any]={}
        form["service"]=self.config["service_name"]
        form["type"] = "Form"
        form["formid"] = newformname
        form["callback"] = "serviceSelected"
        form["title"] = newform[0]["title"]
        form["subtitle"] = newform[0].get("subtitle","")    
        form["widgets"]=newform
        
        for widgetid, widget in enumerate(form["widgets"]):
            if widget["type"]=="Menu":
                widget_name = widget.get("name",widget.get("widget_name",""))
                for choiceid,choice in enumerate(widget["choices"]):
                    datainfo = choice.get("data","")
                    if datainfo[:2] == "##" and datainfo[-2:] == "##":
                        infoProvider = datainfo[2:-2]
                        if infoProvider in self.infoProviders.keys():
                            infoFunction = self.infoProviders[infoProvider]
                            if True or infoFunction in globals():
                                form["widgets"][widgetid]["choices"][choiceid]["data"] = str(self.infoProviders[infoProvider]())
                            else:
                                raise NameError(f"infoProvider not defined in globals() : form:[{newformname}] widget:[{widget_name}] choice:[{choice['label']}] infoProvider key:({infoProvider})infoProvider function:[{infoFunction}]") 
                        else: 
                            raise NameError(f"infoProvider not registered : form:[{newformname}] widget:[{widget_name}] choice:[{choice['label']}] infoProvider:[{infoProvider}]") 

        response_message:dict[str,Any|str]={}
        response_message = {"form": form}
        response_message["action"] = "UpdateForm"
        response_message["service_name"] = self.config["service_name"]
        json_message = json.dumps(response_message)
        # send new form to serviceUIwebserver
        with open(self.config["response_fifo_path"] , "w") as f:
            f.write(json_message)
            
    
        # Process the message
        # message format : {command: "text_input_action",
        #                   value: "Hello",
        #                   context: ["key1", "value1"],["key2", "value2"]}
        # commands : registration_confirmed, 
        #            start-
        # 
                   
    def run(self):
        # Register services
        self.register_service()
        # Start a thread to handle messages from the connectorFifoPath
        self.listen_to_connector()

    def quit(self):
        self.quitRequested = True
    def registerInfo(self,infoProviders:dict):
        self.infoProviders= self.infoProviders | infoProviders


    def __init__(self,serviceConfig:dict[str,Any],formsConfig:dict[str,Any]):
        super().__init__()
        # Read config file
        self.config = self.merge_configs(serviceConfig,formsConfig) 

        self.infoProviders:dict={}
        self.service_list_display = []
        self.text_inputs = []
        self.text_blocks = []
        self.quitRequested = False
        fifo_dir_name = self.config.get("serviceUIconnector_fifo_basepath", tempfile.gettempdir())
        fifo_file_name = self.config["service_name"] + "_connector.fifo"
        fifo_full_path = os.path.join(fifo_dir_name, fifo_file_name)
        if not os.path.exists(fifo_full_path):
            os.makedirs(fifo_dir_name, exist_ok=True)            
            os.mkfifo(fifo_full_path)
        self.serviceFifo_path = fifo_full_path

def start_serviceUIconnector(serviceConfig:dict[str,Any],formsConfig:dict[str,Any]):
    # start serviceUIconnector asyc in a thread.
    # call app.quit() to stop it. 
    app = serviceUIconnector(serviceConfig,formsConfig)
    app.start()
    return app




if __name__ == "__main__":
    print("This is a module, not a standalone script.")
