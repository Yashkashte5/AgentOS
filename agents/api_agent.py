import requests
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from graph.state import AgentState
from config import GROQ_API_KEY, LIGHT_MODEL


class APICall(BaseModel):
    url: str = Field(description="Full URL including path")
    method: str = Field(description="HTTP method: GET or POST")
    params: dict = Field(default={}, description="Query parameters")
    headers: dict = Field(default={}, description="Request headers")


llm = ChatGroq(model=LIGHT_MODEL, api_key=GROQ_API_KEY, temperature=0)
structured_llm = llm.with_structured_output(APICall)

SYSTEM = """You are an API agent. Your job is to construct a correct HTTP API call to retrieve the requested real-time data.

RULES:
- Use only free public APIs that require zero authentication and no API key
- Always construct a complete, valid URL with all required path segments and query parameters
- Choose the most reliable and well-known API for the data type:
  • Cryptocurrency prices  → https://api.coinbase.com/v2/prices/{crypto}-USD/spot  (e.g. BTC-USD, ETH-USD)
  • Weather               → https://wttr.in/{city}?format=j1
  • IP geolocation        → https://ipapi.co/json/
  • Public holidays       → https://date.nager.at/api/v3/PublicHolidays/{year}/{countryCode}
  • Random facts/jokes    → https://official-joke-api.appspot.com/random_joke
  • Country info          → https://restcountries.com/v3.1/name/{country}
  • Exchange rates        → https://open.er-api.com/v6/latest/USD
- Set method to GET unless POST is explicitly required
- Never add an Authorization header — these are public APIs
- If you are not confident in the exact correct URL for an API, use the most standard and documented form"""

def api_node(state: AgentState) -> dict:
    task = state["task"]

    result = ""
    try:
        api_call: APICall = structured_llm.invoke([
            SystemMessage(content=SYSTEM),
            HumanMessage(content=f"Task: {task}")
        ])

        response = requests.request(
            api_call.method,
            api_call.url,
            params=api_call.params,
            headers=api_call.headers,
            timeout=10
        )

        if response.status_code == 200:
            result = response.text[:2000]
        else:
            result = f"API returned status {response.status_code}: {response.text[:500]}"

    except requests.exceptions.Timeout:
        result = "API call timed out after 10s"
    except requests.exceptions.ConnectionError:
        result = "API call failed: could not connect to the server"
    except Exception as e:
        result = f"API call failed: {str(e)}"

    outputs = state.get("agent_outputs", {})
    outputs["api"] = result
    current = state.get("current_step", 0)

    return {
        "agent_outputs": outputs,
        "current_step": current + 1,
    }