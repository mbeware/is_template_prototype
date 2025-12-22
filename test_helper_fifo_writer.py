import helper_fifo
import datetime
import time


fifolog = helper_fifo.MyFifoHandler("/tmp/test_fifo")

fifolog.open_fifo(helper_fifo.FifoMode.WRITE)


timeout_time = datetime.datetime.now() + datetime.timedelta(seconds=30)
timed_out = False
while (not timed_out): 
    fifolog.write_fifo(f"({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) testing")
    time.sleep(1)
    timed_out = datetime.datetime.now() > timeout_time

fifo_signal = helper_fifo.MyFifoHandler("/tmp/signal_fifo")
fifolog.open_fifo(helper_fifo.FifoMode.READ)


