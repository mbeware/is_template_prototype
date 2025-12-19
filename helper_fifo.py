import asyncio
import datetime
import json
import os
from enum import Enum
from time import time
from typing import Any

TIMEOUT_DELAY_SECONDS = 10

# enums 
class SignalEnum(Enum):
    MESSAGE_SENT = "MESSAGE_SENT"
    MESSAGE_RECEIVED = "MESSAGE_RECEIVED"
    TIME_OUT = "TIME_OUT"
    QUIT = "QUIT"
    NOTHING_YET = "NOTHING_YET"

class SignalChannel:
    def __init__(self):
        self.lastSignal:SignalEnum = SignalEnum.NOTHING_YET
        
    def setSignal(self, signal:SignalEnum):
        self.lastSignal = signal    
    
    def getSignal(self) -> SignalEnum:
        return self.lastSignal  
    
    def clearSignal(self):  
        self.lastSignal = SignalEnum.NOTHING_YET    


class FifoErrors(Enum):
    FIFO_NOT_CREATED = "FIFO_NOT_CREATED"
    FIFO_NOT_OPENED  = "FIFO_NOT_OPENED"
    FIFO_NOT_READ_MODE = "FIFO_NOT_READ_MODE"
    FIFO_NOT_WRITE_MODE = "FIFO_NOT_WRITE_MODE"
    FIFO_READ_ERROR = "FIFO_READ_ERROR"
    FIFO_WRITE_ERROR = "FIFO_WRITE_ERROR"
    FIFO_TIMEOUT = "FIFO_TIMEOUT"
    FIFO_CANCELLED = "FIFO_CANCELLED"
    FIFO_OK = "FIFO_OK"



class FifoMode(Enum):
    READ = 'r'
    WRITE = 'w'

class MyFifoHandler:
    def __init__(self, fifo_path:str):
        self.fifo_path = fifo_path
        self.opened_fifo = None
        self.fifo_mode:FifoMode|None = None
        self.fifo_data_available    = False
        self.read_async_running = True
        self.async_loop = None
        self.signal_channel = SignalChannel()
        self.fifo_data              = ""
        self.quitRequested          = False
        if not self.create_fifo():
            raise Exception(f"Could not create fifo at path '{fifo_path}'") 
         

    def create_fifo(self, fifo_path:str|None=None) -> str|None:
        if not fifo_path:
            fifo_path = self.fifo_path
        if not os.path.exists(fifo_path):
            dirname = os.path.dirname(fifo_path)
            os.makedirs(dirname, exist_ok=True)
            try:
                os.mkfifo(fifo_path) 
            except FileExistsError:
                pass    
            except Exception as e:
                return str(e)
        return None

    def close_fifo(self):
        self.opened_fifo.close() # type: ignore
    
    def open_fifo(self, mode:FifoMode) -> str|None:
        if self.opened_fifo:
            self.close_fifo()
        try:
            self.opened_fifo = open(self.fifo_path, mode.value)
            self.fifo_mode = mode
        except Exception as e:
            return str(e)
        return None
    
    def stop_async_read(self):
        try:
            self.async_loop.remove_reader(self.opened_fifo.fileno()) # type: ignore
            self.async_loop.stop() # type: ignore
        except Exception as e:
            pass
        finally:
            self.async_loop = None
            self.read_async_running = False
    
    def read_async_fifo(self,callback_event) -> str|None:
        if self.read_async_running:
            return "Async read already running"
        if not self.opened_fifo:
            self.open_fifo(FifoMode.READ)
        elif self.fifo_mode != FifoMode.READ:
            return "FIFO not opened in read mode"
        
        async def start_async_read():
            self.read_async_running = True
            self.async_loop = asyncio.get_event_loop()
            def get_data():
                
                try:
                    data = self.opened_fifo.read() # type: ignore
                    if data:
                        self.fifo_data = data
                        self.fifo_data_available = True
                        self.signal_channel.setSignal(SignalEnum.MESSAGE_RECEIVED)
                        callback_event(self)
                    else:
                        pass
                except Exception as e:
                    print(f"Error reading from FIFO: {e}")
                    self.stop_async_read()                                                  
            
            # Add the reader to the event loop
            self.async_loop.add_reader(self.opened_fifo.fileno(), get_data) # type: ignore
            # Keep the loop running
            await asyncio.Event().wait()
        asyncio.run(start_async_read())
        return None
   
    def read_once_fifo(self) -> str|None:
        if not self.opened_fifo:
            return "FIFO not opened"
        if self.fifo_mode != FifoMode.READ:
            return "FIFO not opened in read mode"
        try:

            data = self.opened_fifo.read()
            if data :
                self.fifo_data = data
                return None
            return "No data"
        except Exception as e:
            return str(e)
           
    
    def write_fifo(self, message:str) -> str|None: 
        if self.fifo_mode != FifoMode.WRITE:
            return "FIFO not opened in write mode"
        try:
            self.opened_fifo.write(message) # type: ignore
            self.opened_fifo.flush() # type: ignore
        except Exception as e:
            return str(e)
        

    def sendMessageAndWait(self, message:dict[str,Any]) -> FifoErrors: 
        if self.fifo_mode != FifoMode.WRITE:
            return FifoErrors.FIFO_NOT_WRITE_MODE
    
        signal_received=SignalEnum.NOTHING_YET

        json_message = json.dumps(message)
        
        self.opened_fifo.write(json_message) # type: ignore
        self.opened_fifo.flush() # type: ignore
        timeout_time = datetime.datetime.now() + datetime.timedelta(seconds=TIMEOUT_DELAY_SECONDS)
        while (signal_received is SignalEnum.NOTHING_YET) and (not timed_out): 
            time.sleep(1)
            signal_received = self.signal_channel.getSignal()
            timed_out = datetime.datetime.now() > timeout_time

        if signal_received is not SignalEnum.NOTHING_YET:
            if signal_received is SignalEnum.MESSAGE_RECEIVED:
                return FifoErrors.FIFO_OK
            else:
                return FifoErrors.FIFO_CANCELLED
        elif timed_out:
            return FifoErrors.FIFO_TIMEOUT
        else:
            raise Exception("Unexpected state in sendMessageAndWait")
    