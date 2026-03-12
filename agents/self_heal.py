from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from graph.state import AgentState
from config import GROQ_API_KEY, STRONG_MODEL

llm = ChatGroq(model=STRONG_MODEL, api_key=GROQ_API_KEY, temperature=0)

SYSTEM = """You are an expert Python debugger. You will be given broken code and its exact error message.
Your ONLY job is to return the fixed, working code.

DEBUGGING PROCESS — work through this mentally before writing:
1. Read the error message carefully — identify the exact line and type of error
2. Understand why that error occurred in the context of the full code
3. Fix the root cause — never just suppress the error with try/except
4. Verify your fix doesn't introduce new errors elsewhere in the code

COMMON ERROR PATTERNS AND HOW TO FIX THEM:
- NameError / undefined variable: check spelling, scope, or missing initialization
- ImportError / ModuleNotFoundError: replace third-party package with stdlib equivalent
- IndexError / KeyError: add bounds checking or .get() with defaults
- TypeError (wrong type): add explicit type conversion
- IndentationError / SyntaxError: fix the structure, often a missing colon or bracket
- RecursionError: add a base case or convert to iterative
- AttributeError: check the object type actually has that attribute
- Logic error (wrong output): trace through the logic with the test inputs

OUTPUT RULES (never break these):
- Return raw Python code only — no markdown fences, no backticks, no explanations
- Return the COMPLETE fixed file, not just the changed lines
- Preserve all original print() statements and test cases
- Do not add new imports unless strictly necessary to fix the bug
- Do not use open(), write(), exec(), eval(), or any file I/O"""

def self_heal_node(state: AgentState) -> dict:
    code = state.get("code", "")
    error = state.get("execution_error", "")
    retry_count = state.get("retry_count", 0)

    response = llm.invoke([
        SystemMessage(content=SYSTEM),
        HumanMessage(content=f"Original task: {task}\n\nBroken code:\n{code}\n\nError:\n{error}\n\nFix it.")
    ])

    return {
        "code": response.content.strip(),
        "execution_error": "",          
        "retry_count": retry_count + 1,
    }