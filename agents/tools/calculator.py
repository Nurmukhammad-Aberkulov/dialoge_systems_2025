# tools/calculator.py
from langchain.tools import tool

@tool
def calculator(expression: str) -> float:
    """Evaluate a simple mathematical expression like '3 * (4 + 5)'."""
    try:
        return eval(expression)
    except Exception as e:
        return f"Error: {str(e)}"
