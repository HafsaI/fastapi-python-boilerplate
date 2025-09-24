"""
Example of a simple AI agent implementation.
"""
from typing import Dict, Any
from app.core.base import AgentBase


class SimpleTextProcessor(AgentBase):
    """A simple text processing agent."""
    
    def __init__(self, agent_id: str = "simple-text-processor"):
        super().__init__(
            agent_id=agent_id,
            name="Simple Text Processor",
            description="Processes text input and returns formatted output"
        )
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the text processing."""
        text = input_data.get("text", "")
        
        if not text:
            raise ValueError("No text provided")
        
        # Simple text processing
        processed_text = text.upper().strip()
        word_count = len(processed_text.split())
        
        return {
            "processed_text": processed_text,
            "word_count": word_count,
            "original_length": len(text),
            "processed_length": len(processed_text)
        }
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data."""
        return "text" in input_data and isinstance(input_data["text"], str)


class MathCalculator(AgentBase):
    """A simple math calculator agent."""
    
    def __init__(self, agent_id: str = "math-calculator"):
        super().__init__(
            agent_id=agent_id,
            name="Math Calculator",
            description="Performs basic mathematical operations"
        )
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute mathematical calculation."""
        operation = input_data.get("operation")
        a = input_data.get("a")
        b = input_data.get("b")
        
        if not all([operation, a is not None, b is not None]):
            raise ValueError("Missing required fields: operation, a, b")
        
        try:
            a, b = float(a), float(b)
        except (ValueError, TypeError):
            raise ValueError("a and b must be numbers")
        
        result = self._calculate(operation, a, b)
        
        return {
            "operation": operation,
            "a": a,
            "b": b,
            "result": result
        }
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data."""
        required_fields = ["operation", "a", "b"]
        return all(field in input_data for field in required_fields)
    
    def _calculate(self, operation: str, a: float, b: float) -> float:
        """Perform the mathematical operation."""
        operations = {
            "add": lambda x, y: x + y,
            "subtract": lambda x, y: x - y,
            "multiply": lambda x, y: x * y,
            "divide": lambda x, y: x / y if y != 0 else float('inf'),
            "power": lambda x, y: x ** y,
        }
        
        if operation not in operations:
            raise ValueError(f"Unsupported operation: {operation}")
        
        return operations[operation](a, b)


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Create agents
        text_processor = SimpleTextProcessor()
        calculator = MathCalculator()
        
        # Test text processor
        text_result = await text_processor.execute({
            "text": "Hello World! This is a test."
        })
        print("Text Processor Result:", text_result)
        
        # Test calculator
        calc_result = await calculator.execute({
            "operation": "add",
            "a": 10,
            "b": 5
        })
        print("Calculator Result:", calc_result)
    
    asyncio.run(main())
