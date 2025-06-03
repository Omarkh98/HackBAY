import os
from enum import Enum
from dataclasses import dataclass, fields
from typing import Any, Optional, Dict 

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from dataclasses import dataclass

from dotenv import load_dotenv
load_dotenv()
DEFAULT_REPORT_STRUCTURE = """Use this structure to create a report on the user-provided topic:

1. Introduction (no research needed)
   - Brief overview of the topic area

2. Main Body Sections:
   - Each section should focus on a sub-topic of the user-provided topic
   
3. Conclusion
   - Aim for 1 structural element (either a list of table) that distills the main body sections 
   - Provide a concise summary of the report"""

class SearchAPI(Enum):
    PERPLEXITY = "perplexity"
    TAVILY = "tavily"
    EXA = "exa"
    ARXIV = "arxiv"
    PUBMED = "pubmed"
    LINKUP = "linkup"
    DUCKDUCKGO = "duckduckgo"
    GOOGLESEARCH = "googlesearch"

@dataclass(kw_only=True)
class Configuration:
    """The configurable fields for the chatbot."""
    # Common configuration
    report_structure: str = DEFAULT_REPORT_STRUCTURE # Defaults to the default report structure
    search_api: SearchAPI = SearchAPI.PUBMED # Default to TAVILY
    search_api_config: Optional[Dict[str, Any]] = None
    
    # Graph-specific configuration
    number_of_queries: int = 1 # Number of search queries to generate per iteration
    max_search_depth: int = 2 # Maximum number of reflection + search iterations
    recursion_limit: int = 30 # Maximum recursion limit for the search
    planner_provider: str = "groq"  # Defaults to Anthropic as provider
    planner_model: str = "llama-3.3-70b-versatile" # Defaults to claude-3-7-sonnet-latest
    planner_model_kwargs: Optional[Dict[str, Any]] = None # kwargs for planner_model
    writer_provider: str = "groq" # Defaults to Anthropic as provider
    writer_model: str = "llama-3.3-70b-versatile" # Defaults to claude-3-5-sonnet-latest

    # Use Ollama models by default
    # writer_provider: str = "ollama" 
    # writer_model: str = "ollama:llama2" 
    # planner_provider: str = "ollama"
    # planner_model: str = "ollama:llama2"
    # planner_model_kwargs: Optional[Dict[str, Any]] = None
    # writer_model_kwargs: Optional[Dict[str, Any]] = None 

    # supervisor_model: str = os.getenv("SUPERVISOR_MODEL", "ollama:llama2")
    # researcher_model: str = os.getenv("RESEARCHER_MODEL", "ollama:llama2")

    
    writer_model_kwargs: Optional[Dict[str, Any]] = None # kwargs for writer_model
    search_api: SearchAPI = SearchAPI.PUBMED # Default to TAVILY
    search_api_config: Optional[Dict[str, Any]] = None 
    
    # Multi-agent specific configuration
    # supervisor_model: str = "openai:gpt-4.1-mini" # Model for supervisor agent in multi-agent setup
    # researcher_model: str = "openai:gpt-4.1-mini" # Model for research agents in multi-agent setup 
    supervisor_model: str = os.getenv("SUPERVISOR_MODEL", "openai:gpt-4.1-mini")  # Model for supervisor agent in multi-agent setup
    print("SUPERVISOR_MODEL", supervisor_model)
    researcher_model: str = os.getenv("RESEARCHER_MODEL", "openai:gpt-4.1-mini")  # Model for research agents in multi-agent setup
    
    # supervisor_model: str = os.getenv("SUPERVISOR_MODEL", "openai:gpt-4.1-mini")
    # researcher_model: str = os.getenv("RESEARCHER_MODEL", "openai:gpt-4.1-mini")
    # ===== CUSTOM ENDPOINT =====
    # custom_base_url: Optional[str] = None  # override OPENAI_API_BASE
    # custom_api_url: Optional[str] = None   # if you need to hit a non‐standard path

     # MCP configuration
    #mcp_servers: Optional[Dict[str, Dict[str, Any]]] = field(default_factory=default_mcp_servers)
    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }
        return cls(**{k: v for k, v in values.items() if v})