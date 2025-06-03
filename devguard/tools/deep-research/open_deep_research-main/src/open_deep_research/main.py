# tools/deep_research_tool/main.py

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict

# If your multi-agent graph is in another location, adjust the import accordingly:
from langchain_core.runnables import RunnableConfig
from configuration import SearchAPI
from multi_agent import graph  # ensure this path matches your project structure

# Configure logging (writes to deep_research_tool.log in the same folder)
LOG_FILE = Path(__file__).parent / "deep_research_tool.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

SYSTEM_DIRECTIVE = (
    "You are running in an automated research mode. "
    "Perform any searches needed and then immediately write a concise, structured report. "
    "Do not ask any clarifying questions."
)

def _build_config() -> RunnableConfig:
    """
    Return a RunnableConfig with parameters tuned for automated deep research.
    You can adjust number_of_queries, max_search_depth, etc. as needed.
    """
    extra = {
        "search_api": SearchAPI.TAVILY,
        "number_of_queries": 5,
        "max_search_depth": 2,
        "recursion_limit": 40
    }
    return RunnableConfig(configurable=extra)

async def _invoke_graph(topic: str, config: RunnableConfig) -> str:
    """
    Build the initial state for the multi-agent graph, invoke it, and extract the report.
    Returns the final report as a string (markdown/plain text).
    """
    logger.info("Starting DeepResearch for topic: %s", topic)

    initial_state: Dict[str, Any] = {
        "messages": [
            {"role": "system", "content": SYSTEM_DIRECTIVE},
            {"role": "user", "content": f"Conduct a deep research on the following guideline or policy topic:\n\n{topic}"}
        ],
        "sections": [],
        "completed_sections": []
    }

    try:
        result: Any = await graph.ainvoke(initial_state, config=config)
        # The graph may return a dict with "final_report" or just a string.
        if isinstance(result, dict):
            report = result.get("final_report") or result.get("content")
        elif isinstance(result, str):
            report = result
        else:
            report = None

        if not report:
            logger.error("No report extracted; raw result type: %s", type(result))
            return "[ERROR] No report found."

        logger.info("Completed DeepResearch for topic: %s", topic)
        return report

    except Exception as exc:
        logger.exception("Error during DeepResearch for topic: %s", topic)
        return f"[ERROR] {exc}"

def create_filename(name: str) -> str:
    """
    Create a safe filename: lowercase, replace spaces with underscores, drop invalid characters.
    """
    safe = "".join(c for c in name if c.isalnum() or c in (" ", "-", "_")).rstrip()
    return safe.replace(" ", "_").lower()

def run_research(topic: str, save_path: str = None) -> str:
    """
    Entry point for the tool. Takes a string 'topic' and optionally a 'save_path' for the .md file.
    Returns either the path to the saved Markdown file or an error string.
    """
    if not topic or not topic.strip():
        return "[ERROR] You must provide a non-empty topic string."

    # Build a RunnableConfig
    config = _build_config()

    # Run async graph invocation synchronously
    try:
        report: str = asyncio.run(_invoke_graph(topic.strip(), config))
    except Exception as exc:
        logger.exception("run_research failed for topic: %s", topic)
        return f"[ERROR] {exc}"

    # If the graph itself returned an error message, pass it back
    if report.startswith("[ERROR]"):
        return report

    # Decide where to save. Default: create a 'reports' folder next to this file.
    base_dir = Path(__file__).parent
    reports_dir = base_dir / "reports"
    reports_dir.mkdir(exist_ok=True)

    # Generate a filename
    name =  create_filename(topic)
    filename = f"{name}.md"
    filepath = reports_dir / filename

    # If that file already exists, append a counter to avoid overwriting
    counter = 1
    while filepath.exists():
        filepath = reports_dir / f"{name}_{counter}.md"
        counter += 1

    try:
        # Write the report string to Markdown file
        filepath.write_text(report, encoding="utf-8")
        logger.info("Report saved to: %s", filepath)
        return str(filepath)
    except Exception as exc:
        logger.exception("Failed to save report for topic: %s", topic)
        return f"[ERROR] Could not save report to file: {exc}"
    
if __name__ == "__main__":
    topic = "DATEV GDPR compliance workflow"
    result = run_research(topic)

    if result.startswith("[ERROR]"):
        print("Deep research failed:", result)
    else:
        print("Deep research completed. Report saved at:")
        print(result)
        # You can then open `result` in your preferred Markdown viewer.
