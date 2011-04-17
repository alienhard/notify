"""A simple handler that prints the message to stdout. Useful for debugging."""


class PrintHandler():
    
    def __init__(self):
        pass
        
    def handle(self, message):
        print message