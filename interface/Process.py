"""
Discrete process - owned by components
A process is a single, well-defined operation that performs specific business logic.
Processes are executed by components and can be chained together.
"""

class Process:
    """Base class for discrete processes"""
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize a process.
        
        Args:
            name: Name of the process (e.g., 'get_files_from_folder')
            description: Brief description of what this process does
        """
        self.name = name
        self.description = description
        self.result = None
        self.error = None
        self.is_complete = False
    
    def execute(self, *args, **kwargs):
        """
        Execute the process. Override in subclass.
        
        Returns:
            Result of the process execution
        """
        raise NotImplementedError(f"Process '{self.name}' must implement execute() method")
    
    def validate_input(self, *args, **kwargs) -> bool:
        """
        Validate input before execution. Override in subclass if needed.
        
        Returns:
            True if input is valid, False otherwise
        """
        return True
    
    def get_result(self):
        """Get the result of the last execution"""
        return self.result
    
    def get_error(self):
        """Get any error from the last execution"""
        return self.error
    
    def is_successful(self) -> bool:
        """Check if the process completed successfully"""
        return self.is_complete and self.error is None
    
    def __repr__(self):
        status = "✓" if self.is_successful() else "✗" if self.error else "○"
        return f"{status} Process({self.name})"
