# serviceUIinterface.py
from dataclasses import dataclass, field
from enum import Enum

def buildForm(form):
    pass

@dataclass
class Choice:
    label: str
    description: str
    data: str

class WidgetType(Enum): 
    Menu="Menu"
    Text_Input="Text_Input"
    Text_Block="Text_Block"
    Select_Service="Select_Service"

@dataclass
class Widget:
    type: WidgetType # "Menu", "Text_Input", "Text_Block", "Select_Service"
    name: str #entry name in config file
    title: str
    choices: list[Choice]
@dataclass
class Form:
    formid: str
    title: str
    subtitle: str
    widgets: list
    service: str
    type: str
    callback: str 

class ActionType(Enum):
    Register="Register"
    Unregister="Unregister"
    UpdateForm="UpdateForm"

@dataclass
class BaseMessageToUI:
    service_name:str 
    action: ActionType

@dataclass
class RegisterMessageToUI(BaseMessageToUI):
    connectorFifoPath:str # path to connector fifo

@dataclass
class UpdateFormMessageToUI(BaseMessageToUI):
    form: Form

@dataclass
class UnregisterMessageToUI(BaseMessageToUI):
    pass    

@dataclass
class MessageFromUI:
    service: str # service name (should match the service name of the recipient)
    formid: str # form with the activated widget
    widget_name: str # name of the widget activated
    widget_type: WidgetType
    data: str # choice, input_text, etc


