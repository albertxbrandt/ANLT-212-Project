"""
Component module - Starter template for building logical units.
Add your component logic here.
"""


class Component:
    """Base class for components - override in subclasses"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.state = {}
    
    def execute(self, *args, **kwargs):
        """Override this method to implement your component logic"""
        raise NotImplementedError(f"Implement execute() in {self.__class__.__name__}")
