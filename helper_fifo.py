import asyncio
import datetime
import json
import os
from enum import Enum
import time
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
    FIFO_EXCEPTION = "FIFO_EXCEPTION"
    FIFO_READ_ALREADY_IN_PROGRESS = "FIFO_READ_ALREADY_IN_PROGRESS"
    FIFO_NO_DATA = "FIFO_NO_DATA"


class FifoMode(Enum):
    READ = 'r'
    WRITE = 'w'

class FifoCheckState(Enum):
    READ = 'Read'
    WRITE = 'Write'
    READ_ASYNC = 'ReadAsync'

class MyFifoHandler:
    def __init__(self, fifo_path:str):
        self.FifoException:Exception|None = None
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
         
    def check_fifo(self, neededMode:FifoCheckState)->FifoErrors:
        
        if neededMode == FifoCheckState.READ_ASYNC and self.read_async_running:
                return FifoErrors.FIFO_READ_ALREADY_IN_PROGRESS

        requiredFifoMode = FifoMode.WRITE if neededMode == "Write" else FifoMode.READ

        if not self.opened_fifo and self.open_fifo(requiredFifoMode) == FifoErrors.FIFO_EXCEPTION: 
                return FifoErrors.FIFO_EXCEPTION
            
        if self.fifo_mode != requiredFifoMode:
            return FifoErrors.FIFO_NOT_READ_MODE if requiredFifoMode == FifoMode.READ else FifoErrors.FIFO_NOT_WRITE_MODE
        
        return FifoErrors.FIFO_OK

    def create_fifo(self, fifo_path:str|None=None) -> FifoErrors:
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
                self.FifoException = e
                return FifoErrors.FIFO_EXCEPTION
        return FifoErrors.FIFO_OK

    def close_fifo(self):
        self.opened_fifo.close() # type: ignore
    
    def open_fifo(self, mode:FifoMode) -> FifoErrors:
        if self.opened_fifo:
            self.close_fifo()
        try:
            self.opened_fifo = open(self.fifo_path, mode.value)
            self.fifo_mode = mode
        except Exception as e:
            self.FifoException = e
            return FifoErrors.FIFO_EXCEPTION
        
        return FifoErrors.FIFO_OK
        
    
    def stop_async_read(self):
        try:
            self.async_loop.remove_reader(self.opened_fifo.fileno()) # type: ignore
            self.async_loop.stop() # type: ignore
        except Exception as e:
            pass
        finally:
            self.async_loop = None
            self.read_async_running = False
    
    def read_async_fifo(self,callback_event) -> FifoErrors:
        if (result := self.check_fifo(FifoCheckState.READ_ASYNC)) != FifoErrors.FIFO_OK:
            return result
        
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
        return FifoErrors.FIFO_OK
   
    def read_once_fifo(self) -> FifoErrors:
        
        if (result:=self.check_fifo(FifoCheckState.READ)) != FifoErrors.FIFO_OK:
            return result

        try:

            data = self.opened_fifo.read() # type: ignore
            if data :
                self.fifo_data = data
                return FifoErrors.FIFO_OK
            return FifoErrors.FIFO_NO_DATA
        except Exception as e:
            self.FifoException = e
            return FifoErrors.FIFO_EXCEPTION
           
    
    def write_fifo(self, message:str) -> FifoErrors: 
        if (result:=self.check_fifo(FifoCheckState.WRITE)) != FifoErrors.FIFO_OK:
            return result
        try:
            self.opened_fifo.write(message) # type: ignore
            self.opened_fifo.flush() # type: ignore
        except Exception as e:
            self.FifoException = e
            return FifoErrors.FIFO_EXCEPTION
        return FifoErrors.FIFO_OK
        

    def sendMessageAndWait(self, message:str) -> FifoErrors: 
        if (result:=self.check_fifo(FifoCheckState.WRITE)) != FifoErrors.FIFO_OK:
            return result
    
        signal_received=SignalEnum.NOTHING_YET

        self.write_fifo(message)
        timeout_time = datetime.datetime.now() + datetime.timedelta(seconds=TIMEOUT_DELAY_SECONDS)
        timed_out = False
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
    