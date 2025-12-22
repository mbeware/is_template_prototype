import tomllib
from flask import Flask, render_template,render_template_string, request, redirect

import threading
import os
import json
import time
import serviceUIinterface
from typing import Any
import datetime
import queue
from select import select
import colorist
import functools
import copy

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('serviceWebUI')


CONFIG_NAME = "serviceUIwebserver.toml"
serviceUIwebserver_path = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(serviceUIwebserver_path, "config", CONFIG_NAME) # in <thismodule>/config/CONFIG_NAME



def print_f_name(func):
    """Print the runtime of the decorated function"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"{colorist.Color.RED}=============================                                {func.__name__}(){colorist.Color.OFF}")
        return func(*args, **kwargs)
    return wrapper




class serviceUIregister(threading.Thread):
    @print_f_name
    def __init__(self):
        super().__init__() 
        self.queue = queue.SimpleQueue()
        self.selectedService = "webUI"
        self.config=self.load_config(CONFIG_PATH)
#        self.message_received = False
        self.service_list:dict[str,str]={}
        self.service_list_display:dict[str,Any]={"title":"Services","choices":[]}
        self.quitRequested = False
        self.serviceFifo = None
        self.actions:dict=self.define_actions()
        if not os.path.exists(self.config["register_fifo_path"]):
            dirname = os.path.dirname(self.config["register_fifo_path"])
            os.makedirs(dirname, exist_ok=True)
            os.mkfifo(self.config["register_fifo_path"])
        if not os.path.exists(self.config["response_fifo_path"]):
            dirname = os.path.dirname(self.config["response_fifo_path"])
            os.makedirs(dirname, exist_ok=True)
            os.mkfifo(self.config["response_fifo_path"])

    @print_f_name
    def load_config(self,config_path:str)->dict[str,Any]:
        try:
            with open(config_path, "rb") as f:
                return tomllib.load(f)
        except Exception as e:
            print(f"Error loading config file '{config_path}': {e}")
            exit(1)

    @print_f_name
    def define_actions(self)-> dict:
        actions: dict = {"Default": lambda x: print("Default action called")}        
        actions["Register"]=self.action_register
        actions["Unregister"]=self.action_unregister
        actions["UpdateForm"]=self.action_update_form 
        actions["timeout"]=self.action_timeout
        return actions   

    def getServiceFifoPath(self,service)->str:
        path = self.service_list[service]
        if not os.path.exists(path):
            dirname = os.path.dirname(path)
            os.makedirs(dirname, exist_ok=True)
            os.mkfifo(path)
        return path
    
    @print_f_name
    def openServiceFifo(self,service):
        path=self.getServiceFifoPath(service)
        self.serviceFifo=open(path, "w") 

    @print_f_name
    def closeServiceFifo(self):
        if self.serviceFifo:
            self.serviceFifo.close()
            self.serviceFifo=None
    @print_f_name
    def action_timeout(self,dict_message: dict[str,Any]):
        app.received_route = "/timeout"

    @print_f_name
    def action_register(self,dict_message:dict[str,Any]):
        # if action==Register message will also contain the following key:
        #                   connectorFifoPath:"<webServerFifoPath>"
            self.service_list[dict_message["service_name"]] = dict_message["connectorFifoPath"]
            service_display ={"label":dict_message["service_name"],
                            "description": dict_message["service_name"],
                            "data":dict_message["connectorFifoPath"]}
            self.service_list_display["choices"].append(copy.deepcopy(service_display))

    @print_f_name
    def action_update_form(self,dict_message:dict[str,Any]):
        # if action==Register message will also contain the following key:
        #           form:"<fully formed form>"
        #           route:"<route>"

        app.currentFormid = dict_message["form"]["formid"]
        app.currentForm = dict_message["form"]
        #app.received_route = dict_message["route"]
        self.message_received = True
    @print_f_name
    def action_unregister(self,dict_message:dict[str,Any]):
        # if action==Unregister message will also contain the following key:
        #                   service_name:"<service_name>"
        service_name = dict_message["service_name"]
        if service_name in self.service_list:
            del self.service_list[service_name]
            # also remove from display list
            for i,service in enumerate(self.service_list_display["choices"]):
                if service["label"]==service_name:
                    del self.service_list_display["choices"][i]
                    break

    @print_f_name
    def waitfor_message_with_timeout(self,path,timeout=10)->str:
        
        data = ""
    
        
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        

        try:
            with os.fdopen(fd, 'r') as f:
                ready, _, _ = select([f], [], [], timeout)
                if not ready:
                    logger.debug(f'Rien reçu sur {path} ')
                    return ""
                data = f.read() 
                if data is None: 
                    data = ""
                return data
        except Exception as e:
            logger.error(f"unknown error {e}")
            return ""
        
                
    @print_f_name
    def waitfor_message(self,path)->str:
        data = ""
        
        with open(path, "r") as f:
            data = f.read() if not None else ""
        return data
        
            


    @print_f_name
    def act_on_message(self,message):
        if not message or message == "": 
            logger.debug("No message to act on") 
            return # no message to act on
        message = message.replace("'", "\"")
        logger.debug("Message received : ",message) 
        # message format : "{service_name:"<service_name>", 
        dict_message = json.loads(message)
        # message format : "{service_name:"<service_name>", 
        #                   action:"<action>",}
        requested_action = dict_message.get("action",None)
        if requested_action is None:
            logger.error(f"Invalid Message : no action'{message}'")
            return
        if requested_action in self.actions:
            self.actions[requested_action](dict_message)
        else:
            logger.error(f"Unknown action '{requested_action}'")


    @print_f_name
    def run(self):
        logger.info(f"Start listening on fifo at {self.config['register_fifo_path']}")
        while not self.quitRequested:
            #send pending messages
            #while not self.queue.empty():
            #        self.sendMessage(self.queue.get())

            
             
            #json_message = self.waitfor_message(self.config['register_fifo_path']) if not None else ""
            json_message = self.waitfor_message_with_timeout(self.config['register_fifo_path'],self.config['register_fifo_timeout']) if not None else ""

            if json_message != "":
                logger.debug(f"Received message on fifo at {self.config['register_fifo_path']} : {json_message}")
                
                self.act_on_message(json_message)
        print("Service UI connector stopped")

    @print_f_name
    def getRegisteredServices(self) -> dict[str,Any] : 
        theList = copy.deepcopy(self.service_list_display)
        return theList

    @print_f_name
    def selectService(self,service_name:str|None=None):
        self.selectedService=service_name

        
    @print_f_name
    def sendMessageAndWaitForResponse(self, message:dict[str,Any]): 
        self.sendMessage(message)
        response = self.waitfor_message_with_timeout(self.config['response_fifo_path'],self.config['response_fifo_timeout'])
        logger.debug(f"Received response on fifo at {self.config['response_fifo_path']} : {response}")
        return response
    
    @print_f_name
    def sendMessageAndActOnResponse(self, message:dict[str,Any]): 
        response_message = self.sendMessageAndWaitForResponse(message)
        if response_message != "":
            # act on the response message
            self.act_on_message(response_message)


    @print_f_name
    def sendMessage(self, message:dict[str,Any]): 
        if self.selectedService == app.registeringProcess.config["WEBUISERVICE"]:
            logger.error(f"Error : selectedService is invalid ({self.selectedService})")
            return
        self.openServiceFifo(self.selectedService)   
        if self.serviceFifo: 
            json_message = json.dumps(message)
            self.serviceFifo.write(json_message)
            self.closeServiceFifo()

    
        


    @print_f_name
    def queueMessage(self,message:dict[str,Any]):
        self.queue.put(message)




                
class myFlask(Flask):
    @print_f_name
    def __init__(self,name:str):
        Flask.__init__(self,name)
        self.registeringProcess = serviceUIregister()
        self.registeringProcess.start()
        self.selectedService:str|None=None
        self.currentFormid=self.registeringProcess.config["WEBUIFORMID"]
        self.currentForm=self.selectServiceForm(self.registeringProcess.getRegisteredServices())
        self.received_route="/"
        with open ("./templates/dynaform.html","r") as f:
            self.dynhtml = f.read()
    
    @print_f_name
    def printform(self,form:dict[str,Any]):
        logger.debug(form)
        logger.debug("***************")
        for formattr in form.keys():
            if formattr == "widgets":
                widgets = form[formattr] # list
                for widget in widgets:
                    wname = widget["name"]
                    for wattr in widget.keys():
                        if wattr == "choices":
                            for choice in widget[wattr]:
                                logger.debug(f"...{wname}...{wattr}...{choice}")
                        else:    
                            logger.debug(f"...{wname}...{wattr}={widget[wattr]}")

            else:
                logger.debug(f"{formattr}={form[formattr]}")

    @print_f_name
    def selectServiceForm(self,service_list=None)-> dict[str,Any]:
        
        if not service_list:
            widgetService = self.registeringProcess.getRegisteredServices()
            service_list=widgetService["choices"]
        form:dict[str,Any]={}
        form["service"]=self.registeringProcess.config["WEBUISERVICE"]
        form["type"] = "Form"
        form["formid"] = self.registeringProcess.config["WEBUIFORMID"]
        form["callback"] = "serviceSelected"
        form["title"] = "List of registered services"
        form["subtitle"] = "select a service"    
        form["widgets"]=[{"type":"Menu","name":"service_select","title":"Select a service","choices":service_list}]
        return form
    @print_f_name
    def navMenuToSelectService(self)-> list[dict[str,Any]]:
        toolbar = []
        navWidget:dict[str,Any]={}
        
        navWidget["type"] = "Menu"
        navWidget["name"] = self.registeringProcess.config["WEBUIBACKTOSELECT"]
        navWidget["title"] =""
        navWidget["choices"]=[{"label" : self.registeringProcess.config["WEBUIFORMID"], 
                                "description" : "Go to List of registered services" }
                                ]
        toolbar.append(navWidget)          
        return toolbar

        


app = myFlask(__name__)        
#app = Flask(__name__)        

# In real implementation this is replaced with named pipe logic
LIVE_LOGS = ["Booting...", "Loading modules...", "Ready."]



@app.route("/")
@print_f_name
def index():
    form : dict[str,Any] = {}
    if (app.currentFormid==app.registeringProcess.config["WEBUIFORMID"]) or (not app.selectedService):
        widgetService = app.registeringProcess.getRegisteredServices()
        form = app.selectServiceForm(widgetService["choices"])
    
    else : 
        form = copy.deepcopy(app.currentForm)
        navmenu = app.navMenuToSelectService()
        form["widgets"].extend(navmenu)
    app.printform(form)
    return render_template_string(app.dynhtml, **form)
#    return render_template("screen.html", **ctx)


# ----- MENU ACTION ---------------------------------------------------------

@app.route("/menu_action", methods=["POST"])
@print_f_name
def menu_action():
    route = "/"
    choice = request.form.get("choice")
    service = request.form.get("service")
    formid = request.form.get("formid")
    widgetname = request.form.get("widget_name")
    if widgetname == app.registeringProcess.config["WEBUIBACKTOSELECT"] and choice == app.registeringProcess.config["WEBUIFORMID"] : 
        app.registeringProcess.selectService()
        app.currentFormid=choice
        route = "/"
    else:
        if app.currentFormid == app.registeringProcess.config["WEBUIFORMID"]:
            service = choice
            app.registeringProcess.selectService(service)
            app.selectedService=service

        message={"service":service,"formid":formid,"widget_type":"menu","widget_name":widgetname,"choice":choice}        
        app.registeringProcess.sendMessageAndActOnResponse(message)
    return redirect(route)


# ----- TEXT INPUT ACTION ---------------------------------------------------
@app.route("/text_input_action", methods=["POST"])
@print_f_name
def text_input_action():
    value = request.form.get("value")
    logger.debug(f"[FR] Texte reçu: {value}")
    # TODO: send to pipe
    return redirect("/")


# ----- TEXT BLOCK AUTO REFRESH ---------------------------------------------
@app.route("/refresh_block")
@print_f_name
def refresh_block():
    idx = int(request.args.get("index", 1))
    # TODO: read actual logs from service FIFO
    return "\n".join(LIVE_LOGS)

@app.route("/timeout")
@print_f_name
def timeout():
    app.registeringProcess.selectService()
    return render_template("timeout.html")    





if __name__ == "__main__":
                
    app.run(debug=False, port=5000)    
#    app.run(debug=True,use_reloader=False,port=5000)

