"""
Page module - Starter template for building page structures.
Add your page logic here.
"""


class Page:
    """Base class for pages - override in subclasses"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    def render(self):
        """Override this method to implement your page rendering logic"""
        raise NotImplementedError(f"Implement render() in {self.__class__.__name__}")