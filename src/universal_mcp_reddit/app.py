from universal_mcp.applications import APIApplication
from universal_mcp.integrations import Integration

class RedditApp(APIApplication):
    """
    Base class for Universal MCP Applications.
    """
    def __init__(self, integration: Integration = None, **kwargs) -> None:
        super().__init__(name="reddit", integration=integration, **kwargs)

    def run(self):
        """
        Example tool implementation.
        """
        print(f"Running the main task for {self.name}...")
        print("Hello from RedditApp!")
        return "Task completed successfully."

    def list_tools(self):
        """
        Lists the available tools (methods) for this application.
        """
        return [self.run]
