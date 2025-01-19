# This function is not intended to be invoked directly. Instead it will be
# triggered by an orchestrator function.
# Before running this sample, please:
# - create a Durable orchestration function
# - create a Durable HTTP starter function
# - add azure-functions-durable to requirements.txt
# - run pip install -r requirements.txt


import logging
import os
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
from langchain.tools import Tool, tool
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from pydantic import BaseModel, Field
from langchain_community.utilities import BingSearchAPIWrapper
from langchain import hub
from langchain.agents import AgentExecutor, create_tool_calling_agent

AZURE_OPENAI_KEY = os.environ["AZURE_OPENAI_KEY"] 
AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"] 
AZURE_OPENAI_DEPLOYMENT = os.environ["AZURE_OPENAI_DEPLOYMENT"] 
AZURE_OPENAI_VERSION = os.environ["AZURE_OPENAI_VERSION"] 
AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT = os.environ["AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT"] 

llm = AzureChatOpenAI(
            openai_api_version=os.environ["AZURE_OPENAI_VERSION"],
            openai_api_key=os.environ["AZURE_OPENAI_KEY"],
            azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"]
        )

@tool
def call_web_seach(query: str):
        """web search for questions."""
        search = BingSearchAPIWrapper(k=10)
        search_results = search.run(query)
        return search_results

tools = [call_web_seach]

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are very powerful assistant, but don't know current events",
        ),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# Create an agent by passing in the language model and tools
agent = create_tool_calling_agent(llm, tools, prompt)
# Create an agent executor by passing in the agent and tools
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

def main(name: str) -> str:
    #print(name)
    policies = json.loads(name)
    policy=policies.get('policy')

    # Create an agent executor by passing in the agent and tools
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

    industry_risk_analysis_result = agent_executor.invoke(
        {
            "input": "Based on the policy's industry trend ,advice if should be approved or not:" + str(policy)
        }
        )

    industry_risk_analysis_agent_decesion = industry_risk_analysis_result['output']

    print("################################################")
    print("Done analysiing industry risk analysis for this policies, here are the results:")
    print("################################################")
    print(
        json.dumps({
        "policy": policy,
        "decision": policies.get('decision'),
        "reason": policies.get('reason'),
        "industry_risk_analysis_result": industry_risk_analysis_result['output']
    })
    )
    print("################################################")

    return json.dumps({
        "policy": policy,
        "decision": policies.get('decision'),
        "reason": policies.get('reason'),
        "industry_risk_analysis_result": industry_risk_analysis_result['output'],

    })