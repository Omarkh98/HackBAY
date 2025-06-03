from typing import List, Annotated, TypedDict, operator, Literal
from pydantic import BaseModel, Field

#from langchain.chat_models import init_chat_model
from utils import init_chat_model
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langgraph.graph import MessagesState

from langgraph.types import Command, Send
from langgraph.graph import START, END, StateGraph

from open_deep_research.configuration import Configuration
from open_deep_research.utils import get_config_value, tavily_search, duckduckgo_search, pubmed_search
from open_deep_research.prompts import SUPERVISOR_INSTRUCTIONS, RESEARCH_INSTRUCTIONS

import logging
from pathlib import Path
import json

# Configure logging
LOG_FILE = Path(__file__).parent / 'deepresearch.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

## Tools factory - will be initialized based on configuration
def get_search_tool(config: RunnableConfig):
    """Get the appropriate search tool based on configuration"""
    configurable = Configuration.from_runnable_config(config)
    search_api = get_config_value(configurable.search_api)

    # TODO: Configure other search functions as tools
    if search_api.lower() == "tavily":
        # Use Tavily search tool
        return tavily_search
    elif search_api.lower() == "duckduckgo":
        # Use the DuckDuckGo search tool
        return duckduckgo_search
    elif search_api.lower() == "pubmed":
        # Use the DuckDuckGo search tool
        return pubmed_search
    else:
        # Raise NotImplementedError for search APIs other than Tavily
        raise NotImplementedError(
            f"The search API '{search_api}' is not yet supported in the multi-agent implementation. "
            f"Currently, only Tavily is supported. Please use the graph-based implementation in "
            f"src/open_deep_research/graph.py for other search APIs, or set search_api to 'tavily'."
        )

@tool
class Section(BaseModel):
    name: str = Field(
        description="Name for this section of the report.",
    )
    description: str = Field(
        description="Research scope for this section of the report.",
    )
    content: str = Field(
        description="The content of the section."
    )

@tool
class Sections(BaseModel):
    sections: List[str] = Field(
        description="Sections of the report.",
    )

@tool
class Introduction(BaseModel):
    name: str = Field(
        description="Name for the report.",
    )
    content: str = Field(
        description="The content of the introduction, giving an overview of the report."
    )

@tool
class Conclusion(BaseModel):
    name: str = Field(
        description="Name for the conclusion of the report.",
    )
    content: str = Field(
        description="The content of the conclusion, summarizing the report."
    )

## State
class ReportStateOutput(TypedDict):
    final_report: str # Final report

class ReportState(MessagesState):
    sections: list[str] # List of report sections 
    completed_sections: Annotated[list, operator.add] # Send() API key
    final_report: str # Final report

class SectionState(MessagesState):
    section: str # Report section  
    completed_sections: list[Section] # Final key we duplicate in outer state for Send() API

class SectionOutputState(TypedDict):
    completed_sections: list[Section] # Final key we duplicate in outer state for Send() API

# Tool lists will be built dynamically based on configuration
def get_supervisor_tools(config: RunnableConfig):
    """Get supervisor tools based on configuration"""
    search_tool = get_search_tool(config)
    tool_list = [search_tool, Sections, Introduction, Conclusion]
    return tool_list, {tool.name: tool for tool in tool_list}

def get_research_tools(config: RunnableConfig):
    """Get research tools based on configuration"""
    search_tool = get_search_tool(config)
    tool_list = [search_tool, Section]
    return tool_list, {tool.name: tool for tool in tool_list}

# async def supervisor(state: ReportState, config: RunnableConfig):
#     """LLM decides whether to call a tool or not"""

#     # Messages
#     messages = state["messages"]

#     # Get configuration
#     configurable = Configuration.from_runnable_config(config)
#     supervisor_model_name = get_config_value(configurable.supervisor_model)
    
#     # Initialize the model
#     llm = init_chat_model(model=supervisor_model_name) #
    
#     if state.get("completed_sections") and not state.get("final_report"):
#         logging.info("Sections completed, but no final report yet. Writing introduction and conclusion.")
#         research_complete_message = {"role": "user", "content": "Research is complete. Now write the introduction and conclusion for the report. Here are the completed main body sections: \n\n" + "\n\n".join([s.content for s in state["completed_sections"]])}
#         messages = messages + [research_complete_message]

#     supervisor_tool_list, _ = get_supervisor_tools(config) #
    
#     response_message = await llm.bind_tools(supervisor_tool_list).ainvoke(
#         [
#             {"role": "system",
#              "content": SUPERVISOR_INSTRUCTIONS, #
#             }
#         ]
#         + messages
#     )

#     # Manually parse tool_call.args if they are strings
#     if response_message.tool_calls:
#         for tool_call in response_message.tool_calls:
#             if isinstance(tool_call.args, str):
#                 try:
#                     tool_call.args = json.loads(tool_call.args)
#                 except json.JSONDecodeError as e:
#                     logger.error(f"Failed to parse tool_call.args JSON string in supervisor: '{tool_call.args}'. Error: {e}")
#                     # Optionally, raise an error or handle it by setting args to an empty dict or specific error structure
#                     # For now, we log and let it proceed; Pydantic might catch it if still invalid
#                     # or if the tool cannot handle malformed (but now empty/default) args.
#                     # To be safer, you might want to make the tool call fail explicitly here.
#                     # For example: tool_call.args = {"error": "failed to parse arguments", "original_args": tool_call.args}
#                     # Or re-raise: raise ValueError(f"Invalid tool arguments from LLM: {tool_call.args}") from e

#     return {
#         "messages": [response_message]
#    }
async def supervisor(state: ReportState, config: RunnableConfig):
    """LLM decides whether to call a tool or not"""

    # Messages
    messages = state["messages"]

    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    supervisor_model = get_config_value(configurable.supervisor_model)
      # Initialize the model
    llm = init_chat_model(model=supervisor_model)
    logging.info(f"Supervisor using model: {supervisor_model}")
    
    # If sections have been completed, but we don't yet have the final report, then we need to initiate writing the introduction and conclusion
    # If sections have been completed, but we don't yet have the final report, then we need to initiate writing the introduction and conclusion
    if state.get("completed_sections") and not state.get("final_report"):
        research_complete_message = {"role": "user", "content": "Research is complete. Now write the introduction and conclusion for the report. Here are the completed main body sections: \n\n" + "\n\n".join([s.content for s in state["completed_sections"]])}
        messages = messages + [research_complete_message]

    # Get tools based on configuration
    supervisor_tool_list, _ = get_supervisor_tools(config)
      # Invoke
    response = await llm.bind_tools(supervisor_tool_list).ainvoke(
        [
            {"role": "system",
             "content": SUPERVISOR_INSTRUCTIONS,
            }
        ]
        + messages
    )
    #logging.info(f"Supervisor response structure: {json.dumps(response.model_dump(), indent=2)}")
    logging.info(f"Supervisor response structure: {response}")

    # Convert structured output to string if needed
    # if hasattr(response, 'model_dump'):
    #     logging.info(f"Supervisor response structure: {response}")
    #     return {"messages": [response]}
    # else:
    #     logging.info(f"Supervisor response structure: {response}")
    #     return {"messages": [str(response)]}
    
    # Invoke
    return {
        "messages": [
            await llm.bind_tools(supervisor_tool_list, parallel_tool_calls=False).ainvoke(
                [
                    {"role": "system",
                     "content": SUPERVISOR_INSTRUCTIONS,
                    }
                ]
                + messages
            )
        ]
    }

# async def supervisor_tools(state: ReportState, config: RunnableConfig)  -> Command[Literal["supervisor", "research_team", "__end__"]]:
#     """Performs the tool call and sends to the research agent"""

#     result = []
#     sections_list = []
#     intro_content = None
#     conclusion_content = None
#     logging.info("AAAAA")
#     # Get tools based on configuration
#     _, supervisor_tools_by_name = get_supervisor_tools(config)
    
#     # First process all tool calls to ensure we respond to each one (required for OpenAI)
#     # First process all tool calls to ensure we respond to each one (required for OpenAI)
#     for tool_call in state["messages"][-1].tool_calls:
#         # Get the tool
#         tool = supervisor_tools_by_name[tool_call["name"]]
#         # Perform the tool call - use ainvoke for async tools
#         if hasattr(tool, 'ainvoke'):
#             observation = await tool.ainvoke(tool_call["args"])
#         else:
#             observation = tool.invoke(tool_call["args"])

#         # Append to messages 
#         result.append({"role": "tool", 
#                        "content": observation, 
#                        "name": tool_call["name"], 
#                        "tool_call_id": tool_call["id"]})
        
#         # Store special tool results for processing after all tools have been called
#         if tool_call["name"] == "Sections":
#             sections_list = observation.sections
#         elif tool_call["name"] == "Introduction":
#             # Format introduction with proper H1 heading if not already formatted
#             if not observation.content.startswith("# "):
#                 intro_content = f"# {observation.name}\n\n{observation.content}"
#             else:
#                 intro_content = observation.content
#         elif tool_call["name"] == "Conclusion":
#             # Format conclusion with proper H2 heading if not already formatted
#             if not observation.content.startswith("## "):
#                 conclusion_content = f"## {observation.name}\n\n{observation.content}"
#             else:
#                 conclusion_content = observation.content
    
#     # After processing all tool calls, decide what to do next
#     if sections_list:
#         # Send the sections to the research agents
#         return Command(goto=[Send("research_team", {"section": s}) for s in sections_list], update={"messages": result})
#     elif intro_content:
#         # Store introduction while waiting for conclusion
#         # Append to messages to guide the LLM to write conclusion next
#         result.append({"role": "user", "content": "Introduction written. Now write a conclusion section."})
#         return Command(goto="supervisor", update={"final_report": intro_content, "messages": result})
#     elif conclusion_content:
#         # Get all sections and combine in proper order: Introduction, Body Sections, Conclusion
#         intro = state.get("final_report", "")
#         body_sections = "\n\n".join([s.content for s in state["completed_sections"]])
        
#         # Assemble final report in correct order
#         complete_report = f"{intro}\n\n{body_sections}\n\n{conclusion_content}"
#         logging.info("Complete report: ", complete_report)
#         # Append to messages to indicate completion
#         result.append({"role": "user", "content": "Report is now complete with introduction, body sections, and conclusion."})
#         return Command(goto="supervisor", update={"final_report": complete_report, "messages": result})
        
#     else:
#         # Default case (for search tools, etc.)
#         return Command(goto="supervisor", update={"messages": result})

async def supervisor_tools(state: ReportState, config: RunnableConfig)  -> Command[Literal["supervisor", "research_team", "__end__"]]:
    """Performs the tool call and sends to the research agent"""

    result = []
    sections_list = []
    intro_content = None
    conclusion_content = None

    # Get tools based on configuration
    _, supervisor_tools_by_name = get_supervisor_tools(config)
    
    # First process all tool calls to ensure we respond to each one (required for OpenAI)
    for tool_call in state["messages"][-1].tool_calls:
        # Get the tool
        tool = supervisor_tools_by_name[tool_call["name"]]
        # Perform the tool call - use ainvoke for async tools
        if hasattr(tool, 'ainvoke'):
            observation = await tool.ainvoke(tool_call["args"])
        else:
            observation = tool.invoke(tool_call["args"])

        # Append to messages 
        result.append({"role": "tool", 
                       "content": observation, 
                       "name": tool_call["name"], 
                       "tool_call_id": tool_call["id"]})
        
        # Store special tool results for processing after all tools have been called
        if tool_call["name"] == "Sections":
            sections_list = observation.sections
        elif tool_call["name"] == "Introduction":
            # Format introduction with proper H1 heading if not already formatted
            if not observation.content.startswith("# "):
                intro_content = f"# {observation.name}\n\n{observation.content}"
            else:
                intro_content = observation.content
        elif tool_call["name"] == "Conclusion":
            # Format conclusion with proper H2 heading if not already formatted
            if not observation.content.startswith("## "):
                conclusion_content = f"## {observation.name}\n\n{observation.content}"
            else:
                conclusion_content = observation.content
    
    # After processing all tool calls, decide what to do next
    if sections_list:
        # Send the sections to the research agents
        return Command(goto=[Send("research_team", {"section": s}) for s in sections_list], update={"messages": result})
    elif intro_content:
        # Store introduction while waiting for conclusion
        # Append to messages to guide the LLM to write conclusion next
        result.append({"role": "user", "content": "Introduction written. Now write a conclusion section."})
        return Command(goto="supervisor", update={"final_report": intro_content, "messages": result})
    elif conclusion_content:
        # Get all sections and combine in proper order: Introduction, Body Sections, Conclusion
        intro = state.get("final_report", "")
        body_sections = "\n\n".join([s.content for s in state["completed_sections"]])
        
        # Assemble final report in correct order
        complete_report = f"{intro}\n\n{body_sections}\n\n{conclusion_content}"
        
        # Append to messages to indicate completion
        result.append({"role": "user", "content": "Report is now complete with introduction, body sections, and conclusion."})
        return Command(goto="supervisor", update={"final_report": complete_report, "messages": result})
        
    else:
        # Default case (for search tools, etc.)
        return Command(goto="supervisor", update={"messages": result})
        
async def supervisor_should_continue(state: ReportState) -> Literal["supervisor_tools", END]:
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

    messages = state["messages"]
    last_message = messages[-1]
    #logging.info("supervisor should continue Last message: %s", last_message)

    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls:
        logging.info("supervisor should continue to supervisor_tools Last message: ", last_message)
        return "supervisor_tools"
    # Else end because the supervisor asked a question or is finished
    # else:
    #     return END
    # Else end because the supervisor asked a question or is finished
    # End only after the composite report has been assembled
        # if state.get("final_report"):
        #     return END
        # else:
        #     return "supervisor_tools"
    # else:
    #     #logging.info("supervisor should continue Last message: No", last_message)
    #     content = last_message.content 
    #     logging.info("Supervisor got LLM message : %r", last_message)
    #     logging.info("Supervisor got the final content: %r", content)
    #     return END
    # 2) If we've already assembled the final report, we can stop
    # if last_message.content.startswith("The final report:"): 
    #     state.get("final_report") = last_message.content
    #or last_message.content.startswith("Here is the final report"):
    else:      
        logging.info("Supervisor has assembled the final report, ending workflow.")
        return END


async def research_agent(state: SectionState, config: RunnableConfig):
    """LLM decides whether to call a tool or not"""
    
    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    researcher_model = get_config_value(configurable.researcher_model)
      # Initialize the model
    llm = init_chat_model(model=researcher_model)
    logging.info(f"Research agent using model: {researcher_model}")

    # Get tools based on configuration
    research_tool_list, _ = get_research_tools(config)
    response = await llm.bind_tools(research_tool_list).ainvoke(
        [
            {"role": "system",
             "content": RESEARCH_INSTRUCTIONS.format(section_description=state["section"])
            }
        ]
        + state["messages"]
    )
    logging.info(f"Research agent response structure: {response}")
    return {
        "messages": [response]
    }

# async def research_agent(state: SectionState, config: RunnableConfig):
#     """LLM decides whether to call a tool or not"""
    
#     configurable = Configuration.from_runnable_config(config)
#     researcher_model_name = get_config_value(configurable.researcher_model)
    
#     llm = init_chat_model(model=researcher_model_name) #
#     research_tool_list, _ = get_research_tools(config) #
    
#     response_message = await llm.bind_tools(research_tool_list).ainvoke(
#         [
#             {"role": "system",
#              "content": RESEARCH_INSTRUCTIONS.format(section_description=state["section"]) #
#             }
#         ]
#         + state["messages"]
#     )

#     if response_message.tool_calls:
#         for tool_call in response_message.tool_calls:
#             if isinstance(tool_call.args, str):
#                 try:
#                     tool_call.args = json.loads(tool_call.args)
#                 except json.JSONDecodeError as e:
#                     logger.error(f"Failed to parse tool_call.args JSON string in research_agent: '{tool_call.args}'. Error: {e}")
#                     # Handle as in supervisor
                    
#     return {
#         "messages": [response_message]
#     }

async def research_agent_tools(state: SectionState, config: RunnableConfig):
    """Performs the tool call and route to supervisor or continue the research loop"""

    result = []
    completed_section = None
    
    # Get tools based on configuration
    _, research_tools_by_name = get_research_tools(config)
    
    # Process all tool calls first (required for OpenAI)
    for tool_call in state["messages"][-1].tool_calls:
        # Get the tool
        tool = research_tools_by_name[tool_call["name"]]
        print(f"Tool: {tool}")
        # Perform the tool call - use ainvoke for async tools
        if hasattr(tool, 'ainvoke'):
            observation = await tool.ainvoke(tool_call["args"])
        else:
            observation = tool.invoke(tool_call["args"])
        # Append to messages 
        result.append({"role": "tool", 
                       "content": observation, 
                       "name": tool_call["name"], 
                       "tool_call_id": tool_call["id"]})
        
        # Store the section observation if a Section tool was called
        if tool_call["name"] == "Section":
            completed_section = observation
    
    # After processing all tools, decide what to do next
    if completed_section:
        # Write the completed section to state and return to the supervisor
        #logging.info("Completed section: ", completed_section)
        return {"messages": result, "completed_sections": [completed_section]}
    else:
        # Continue the research loop for search tools, etc.
        #logging.info("Research agent tools: No completed section:", result)
        return {"messages": result}

async def research_agent_should_continue(state: SectionState) -> Literal["research_agent_tools", END]:
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

    messages = state["messages"]
    last_message = messages[-1]
    #logging.info("research_agent should continue Last message: ", last_message)
    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls:
        return "research_agent_tools"

    else:
        #logging.info("research_agent should continue Last message: No")
        return END
    
"""Build the multi-agent workflow"""

# Research agent workflow
research_builder = StateGraph(SectionState, output=SectionOutputState, config_schema=Configuration)
research_builder.add_node("research_agent", research_agent)
research_builder.add_node("research_agent_tools", research_agent_tools)
research_builder.add_edge(START, "research_agent") 
research_builder.add_conditional_edges(
    "research_agent",
    research_agent_should_continue,
    {
        # Name returned by should_continue : Name of next node to visit
        "research_agent_tools": "research_agent_tools",
        END: END,
    },
)
research_builder.add_edge("research_agent_tools", "research_agent")

# Supervisor workflow
supervisor_builder = StateGraph(ReportState, input=MessagesState, output=ReportStateOutput, config_schema=Configuration)
supervisor_builder.add_node("supervisor", supervisor)
supervisor_builder.add_node("supervisor_tools", supervisor_tools)
supervisor_builder.add_node("research_team", research_builder.compile())

# Flow of the supervisor agent
supervisor_builder.add_edge(START, "supervisor")
supervisor_builder.add_conditional_edges(
    "supervisor",
    supervisor_should_continue,
    {
        # Name returned by should_continue : Name of next node to visit
        "supervisor_tools": "supervisor_tools",
        END: END,
    },
)
supervisor_builder.add_edge("research_team", "supervisor")

graph = supervisor_builder.compile()
