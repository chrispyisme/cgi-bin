from abc import ABC, abstractmethod
from typing import List, Dict, Any
import json

# 1. The Component Interface
class Node(ABC):
    """The base interface that all template nodes must implement."""
    @abstractmethod
    def render(self, context: Dict[str, Any]) -> str:
        pass

# 2. The Leaves (Primitives)
class TextNode(Node):
    """Represents raw, static text or HTML."""
    def __init__(self, text: str):
        self.text = text
        
    def render(self, context: Dict[str, Any]) -> str:
        return self.text

class VariableNode(Node):
    """Represents a dynamic variable placeholder (e.g., {{ name }})."""
    def __init__(self, var_name: str):
        self.var_name = var_name
        
    def render(self, context: Dict[str, Any]) -> str:
        # Fetches the value from the datasource dictionary
        return str(context.get(self.var_name, ""))

# 3. The Composite (Branches)
class ElementNode(Node):
    """Represents an HTML/XML tag that can contain multiple child Nodes."""
    def __init__(self, tag_name: str, attributes: Dict[str, str] = None):
        self.tag_name = tag_name
        self.attributes = attributes or {}
        self.children: List[Node] = []
        
    def add_child(self, child: Node) -> None:
        """Adds a child node to the composite's internal list."""
        self.children.append(child)
        
    def render(self, context: Dict[str, Any]) -> str:
        # Format attributes if they exist
        attrs = "".join(f' {k}="{v}"' for k, v in self.attributes.items())
        
        # The Composite magic: iterate through all children and recursively call render()
        inner_content = "".join(child.render(context) for child in self.children)
        
        return f"<{self.tag_name}{attrs}>{inner_content}</{self.tag_name}>"
    
__all__ = ["Node", "TextNode", "VariableNode", "ElementNode"]
