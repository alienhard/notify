"""A simple handler that prints the message to stdout. Useful for debugging."""

import sys
import re

class PrintHandler():
    
    def handle(self, message):
        print message