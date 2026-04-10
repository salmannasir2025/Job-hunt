import sys
from unittest.mock import MagicMock
from types import ModuleType

def mock_package(name):
    m = ModuleType(name)
    m.__path__ = []
    sys.modules[name] = m
    return m

# Mock modules that are difficult to install
mock_modules = [
    "crewai",
    "crewai.tools",
    "crawl4ai",
    "whois",
    "langchain_groq",
    "langchain_openai",
]

for mod in mock_modules:
    if mod not in sys.modules:
        m = mock_package(mod)
        if mod == "crewai":
            m.Agent = MagicMock()
            m.Task = MagicMock()
            m.Crew = MagicMock()
        elif mod == "crewai.tools":
            m.tool = lambda x: x
        elif mod == "crawl4ai":
            m.Crawl4AI = MagicMock()
        elif mod == "langchain_groq":
            m.ChatGroq = MagicMock()
        elif mod == "langchain_openai":
            m.ChatOpenAI = MagicMock()
