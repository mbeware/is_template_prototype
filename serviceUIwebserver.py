from flask import Flask, render_template,render_template_string, request, redirect
from config_loader import load_ui_config
from ui_renderer import prepare_context
import threading
import os
import json
import time
import serviceUIinterface
from typing import Any
import datetime

def selectServiceForm(service_list=None)-> dict[str,Any]:
    if not service_list:
        widgetService = app.registeringProcess.getRegisteredServices()
        service_list=widgetService["choices"]
    form:dict[str,Any]={}
    form["service"]="Not Selected"
    form["type"] = "Form"
    form["formid"] = "SelectService"
    form["callback"] = "serviceSelected"
    form["title"] = "List of registered services"
    form["subtitle"] = "select a service"    
    form["widgets"]=[{"type":"Menu","name":"service_select","title":"Select a service","choices":service_list}]
    return form

class serviceUIregister(threading.Thread):
    def __init__(self):
        super().__init__() 
        print("init serviceUIregister")
        self.config = load_ui_config()
        self.service_list:dict[str,str]={}
        self.service_list_display:dict[str,Any]={"title":"Services","choices":[]}
        self.quitRequested = False
        self.serviceFifo = None
        self.actions:dict=self.define_actions()
        if not os.path.exists(self.config["fifo_path"]):
            dirname = os.path.dirname(self.config["fifo_path"])
            os.makedirs(dirname, exist_ok=True)
            os.mkfifo(self.config["fifo_path"])

    def define_actions(self)-> dict:
        actions: dict = {"Default": lambda x: print("Default action called")}        
        actions["Register"]=self.action_register
        actions["Unregister"]=self.action_unregister
        actions["UpdateForm"]=self.action_update_form 
        return actions   


    def openServiceFifo(self,service):
        path = self.service_list[service]
        if not os.path.exists(path):
            dirname = os.path.dirname(path)
            os.makedirs(dirname, exist_ok=True)
            os.mkfifo(path)
        self.serviceFifo=open(path, "w") 

    def closeServiceFifo(self):
        if self.serviceFifo:
            self.serviceFifo.close()
            self.serviceFifo=None


    def action_register(self,dict_message:dict[str,Any]):
        # if action==Register message will also contain the following key:
        #                   connectorFifoPath:"<webServerFifoPath>"
            self.service_list[dict_message["service_name"]] = dict_message["connectorFifoPath"]
            service_display ={"label":dict_message["service_name"],
                            "description": dict_message["service_name"],
                            "data":dict_message["connectorFifoPath"]}
            self.service_list_display["choices"].append(service_display.copy())

    def action_update_form(self,dict_message:dict[str,Any]):
        # if action==Register message will also contain the following key:
        #           form:"<fully formed form>"
        #           route:"<route>"

        app.currentFormid = dict_message["form"]["formid"]
        app.currentForm = dict_message["form"]
        app.received_route = dict_message["route"]
        self.message_received = True
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
        


    def run(self):
        print(f"Start listening on fifo at '{self.config["fifo_path"]}'")

        with open(self.config["fifo_path"], "r") as f:
            while not self.quitRequested:
                json_message = f.read()
                if json_message != "":
                    print(f"Received message on fifo at '{self.config["fifo_path"]}' : {json_message}")
                    json_message = json_message.replace("'", "\"")
                    dict_message = json.loads(json_message)
                    # message format : "{service_name:"<service_name>", 
                    #                   action:"<action>",}
                    requested_action = dict_message["action"]
                    if requested_action in self.actions:
                        self.actions[requested_action](dict_message)

                time.sleep(1)
                    
        print("Service UI connector stopped")

    def getRegisteredServices(self) -> dict[str,Any] : 
        theList = self.service_list_display.copy()
        return theList

    def selectService(self,service_name:str|None=None):
        self.closeServiceFifo()
        self.selectedService=service_name
        if service_name:
            self.currentFormid = "main"
            self.openServiceFifo(service_name)            
        else:
            app.currentFormid = "SelectService"

        
    def sendMessage(self, message:dict[str,Any]) -> str: 
        route = "/"
        if self.serviceFifo: 
            self.message_received=False
            json_message = json.dumps(message)
            self.serviceFifo.write(json_message)
            timeout = datetime.datetime.now() + datetime.timedelta(seconds=10)
            while (not self.message_received) and (datetime.datetime.now() < timeout): 
                time.sleep(1)

            if self.message_received:
                route = app.received_route
            else:
                route = "/timeout"



        return route


                
class myFlask(Flask):
    def __init__(self,name:str):
        Flask.__init__(self,name)
        self.registeringProcess = serviceUIregister()
        self.registeringProcess.start()
        self.selectedService:str|None=None
        self.currentFormid="SelectService"
        self.currentForm=selectServiceForm(self.registeringProcess.getRegisteredServices())
        self.received_route="/"
        with open ("./templates/dynaform.html","r") as f:
            self.dynhtml = f.read()


app = myFlask(__name__)        
#app = Flask(__name__)        

# In real implementation this is replaced with named pipe logic
LIVE_LOGS = ["Booting...", "Loading modules...", "Ready."]


# form.service = service name
# form.formid = formid
#
def localtest_getMainForm(service:str, formid:str):
    form:dict[str,Any] = {}

    formdef = load_ui_config("config/demoUI.toml")
    form["service"]=service
    form["type"]=formdef[formid]["type"]
    form["formid"] = formdef[formid]["formid"]
    form["callback"] = formdef[formid]["callback"]
    form["title"] = formdef[formid]["title"]
    form["subtitle"] = formdef[formid]["subtitle"]
    form["name"] = formid
    form["widgets"]=[]

    for widget in formdef[formid]["widgets"]:
            formdef[widget["Name"]]["name"]=widget["Name"]
            form["widgets"].append(formdef[widget["Name"]])
            
    return form



@app.route("/")
def index():
    form : dict[str,Any] = {}
    if (app.currentFormid=="SelectService") or (not app.selectedService):
        widgetService = app.registeringProcess.getRegisteredServices()
        form = selectServiceForm(widgetService["choices"])
    else : 
        # Get formdef from service.
        # formdef = app.blabla....
        # pour test, on lit dans config...
        form = app.currentForm
        #localtest_getMainForm(app.selectedService,app.currentFormid)

    return render_template_string(app.dynhtml, **form)
#    return render_template("screen.html", **ctx)


# ----- MENU ACTION ---------------------------------------------------------
@app.route("/menu_action", methods=["POST"])
def menu_action():
    route = "/"
    choice = request.form.get("choice")
    service = request.form.get("service")
    formid = request.form.get("formid")
    widgetname = request.form.get("name")
    if app.currentFormid == "main" and choice == "main.back" : 
        app.registeringProcess.selectService()
        route = "/"
    else:
        if app.currentFormid == "SelectService":
            service = choice
            app.registeringProcess.selectService(service)

        message={"service":service,"formid":formid,"widget_type":"menu","widget_name":widgetname,"choice":choice}        
        route = app.registeringProcess.sendMessage(message)
    return redirect(route)


# ----- TEXT INPUT ACTION ---------------------------------------------------
@app.route("/text_input_action", methods=["POST"])
def text_input_action():
    value = request.form.get("value")
    print(f"[FR] Texte reçu: {value}")
    # TODO: send to pipe
    return redirect("/")


# ----- TEXT BLOCK AUTO REFRESH ---------------------------------------------
@app.route("/refresh_block")
def refresh_block():
    idx = int(request.args.get("index", 1))
    # TODO: read actual logs from service FIFO
    return "\n".join(LIVE_LOGS)

@app.route("/timeout")
def timeout():
    app.registeringProcess.selectService()
    return render_template("timeout.html")    


if __name__ == "__main__":
                
    app.run(debug=False, port=5000)    
#    app.run(debug=True,use_reloader=False,port=5000)

