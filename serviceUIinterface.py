# serviceUIinterface.py
from dataclasses import dataclass, field, asdict
from dataclasses_json import dataclass_json
from enum import Enum
import json




###################################
#
# communication flow : 
# 
# 1. Service register itself to the serviceUIwebserver with a fifopipe to send information request. 
# 2. serviceUIwebserver send a request to the service with the information about the widget it wants to display.
# 3. Service return the information and the widget in json
# 4. Loop to 2. 
#

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

@dataclass_json
@dataclass
class BaseMessageToUI:
    service_name:str 
    action: ActionType
    def is_valid(self) -> bool: 
        return bool(self.action) and bool(self.service_name) and self.action in ActionType
    def to_json(self) -> str:
        json
        return json.dumps(asdict(self))
        
@dataclass_json
@dataclass
class RegisterMessageToUI(BaseMessageToUI):
    connectorFifoPath:str # path to connector fifo
    def is_valid(self) -> bool:
        return bool(self.connectorFifoPath) and super().is_valid()
        
@dataclass
class UpdateFormMessageToUI(BaseMessageToUI):
    form: Form
    def is_valid(self) -> bool:
        return bool(self.form) and super().is_valid()

@dataclass
class UnregisterMessageToUI(BaseMessageToUI):
    pass    

@dataclass
class MessageToService:
    service: str # service name (should match the service name of the recipient)
    formid: str # form with the activated widget
    widget_name: str # name of the widget activated
    widget_type: WidgetType
    data: str # data entered/selected by the user
    @property
    def choice(self):
        return self.data
    @choice.setter
    def choice(self, value):
        self.data = value

    @property
    def value(self):
        return self.data
    @value.setter
    def value(self, value):
        self.data = value

    def is_valid(self) -> bool:
        valid = True
        valid = valid and bool(self.formid) 
        valid = valid and bool(self.widget_name) 
        valid = valid and bool(self.widget_type) and self.widget_type in WidgetType
        valid = valid and bool(self.data)
        return valid
