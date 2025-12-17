import tomli as tomllib
import threading

import os
import tempfile
from contextlib import contextmanager





class serviceUIconnector(threading.Thread):

    def register_service(self,service_name:str|None=None):
        
        # Register the service in the serviceUIwebserver FIFO.
        # get the fifo path from the config file
        if not service_name:
            service_name = self.config["service_name"]

        webServerFifoPath = self.config["fifo_path"]  
        connectorFifoPath = self.config["serviceUIconnector_fifo_path"]  
        # message format : "{service_name:"<service_name>", 
        #                   connectorFifoPath:"<webServerFifoPath>"}

        # write message to webServerFifoPath
        print(f"want to register [Service '{service_name}' with connector fifo at '{connectorFifoPath}'")

        with open(webServerFifoPath, "w") as f:
            f.write(f'{{"service_name":"{service_name}","action":"Register","connectorFifoPath":"{connectorFifoPath}"}}')
        print(f"[Service '{service_name}' registered with connector fifo at '{connectorFifoPath}'")
        
    def load_config(self,path:str|None=None):
        # Load the configuration from a file or other source.
        if not path:
            path = "config/connector.toml"
        with open(path, "rb") as f:
            return tomllib.load(f)
        
    def listen_to_connector(self):
        # start a thread to listen to the connector fifo
        with open(self.config["serviceUIconnector_fifo_path"], "r") as f:
            while not self.quitRequested:
                # Read message from fifo (this is blocking)
                message = f.read()
                print(f"[FR] Message reçu: {message}")
                # Process message
                self.handle_messages(message)
                
    def handle_messages(self, message):
        pass
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

    def __init__(self,config_file:str|None):
        super().__init__()
        # Read config file
        
        self.config = self.load_config(config_file) 
        

        self.service_list_display = []
        self.text_inputs = []
        self.text_blocks = []
        self.quitRequested = False
        if not os.path.exists(self.config["serviceUIconnector_fifo_path"]):
            dirname = os.path.dirname(self.config["serviceUIconnector_fifo_path"])
            os.makedirs(dirname, exist_ok=True)            
            os.mkfifo(self.config["serviceUIconnector_fifo_path"])

        

def start_serviceUIconnector(config_file:str|None=None):
    # start serviceUIconnector asyc in a thread.
    # call app.quit() to stop it. 
    app = serviceUIconnector(config_file)
    app.start()
    return app

if __name__ == "__main__":
    app = start_serviceUIconnector()

