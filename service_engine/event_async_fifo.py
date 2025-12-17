import asyncio
import os

async def read_fifo(fifo_path):
    # Open the FIFO for reading
    with open(fifo_path, 'r') as fifo:
        # Get the file descriptor
        fd = fifo.fileno()
        # Create an event loop
        loop = asyncio.get_event_loop()
        # Register a callback to be called when the FIFO is readable
        def callback():
            try:
                data = fifo.read()
                if data:
                    print(f"Received data: {data}")
                else:
                    # EOF reached, stop monitoring
                    loop.remove_reader(fd)
            except Exception as e:
                print(f"Error reading from FIFO: {e}")
                loop.remove_reader(fd)

        # Add the reader to the event loop
        loop.add_reader(fd, callback)
        # Keep the loop running
        await asyncio.Event().wait()

# Example usage
if __name__ == "__main__":
    fifo_path = "/tmp/myfifo"
    # Ensure the FIFO exists
    if not os.path.exists(fifo_path):
        os.mkfifo(fifo_path)
    # Run the async function
    asyncio.run(read_fifo(fifo_path))   