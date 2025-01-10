# This function is not intended to be invoked directly. Instead it will be
# triggered by an orchestrator function.
# Before running this sample, please:
# - create a Durable orchestration function
# - create a Durable HTTP starter function
# - add azure-functions-durable to requirements.txt
# - run pip install -r requirements.txt

import os
import logging
import psycopg2
import pandas as pd
import json
from psycopg2.extras import RealDictCursor
import decimal
import datetime
from langgraph.graph import Graph, END
from typing import TypedDict, Annotated
import operator
from typing import List
from langchain_openai import ChatOpenAI,AzureChatOpenAI
from langchain_core.messages import HumanMessage
from langchain.agents import Tool
from langchain.tools import Tool, tool
import pandas as pd
from langchain import hub
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain_core.prompts import ChatPromptTemplate
#from langchain_core.pydantic_v1 import BaseModel, Field
from pydantic import BaseModel, Field
from azure.storage.blob import BlobServiceClient, BlobSasPermissions,generate_blob_sas
from datetime import datetime, timedelta
from langchain_community.utilities import BingSearchAPIWrapper
from langchain import hub
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_experimental.utilities import PythonREPL

BING_SUBSCRIPTION_KEY = os.environ["BING_SUBSCRIPTION_KEY"] 
BING_SEARCH_URL = os.environ["BING_SEARCH_URL"] 
AZURE_OPENAI_KEY = os.environ["AZURE_OPENAI_KEY"] 
AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"] 
AZURE_OPENAI_DEPLOYMENT = os.environ["AZURE_OPENAI_DEPLOYMENT"] 
AZURE_OPENAI_VERSION = os.environ["AZURE_OPENAI_VERSION"] 
AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT = os.environ["AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT"] 

# Fetch data from the policy administration system
PGHOST = os.environ["PGHOST"]
PGUSER = os.environ["PGUSER"]
PGPORT =os.environ["PGPORT"]
PGDATABASE = os.environ["PGDATABASE"]
PGPASSWORD = os.environ["PGPASSWORD"]
connectionString = f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}"

repl = PythonREPL()

def main(name: str) -> str:

    code_gen_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You need to write a Python script that queries a PostgreSQL database for wholesale_casualty_insurance_policies data.
            round the deciamls in in to whole numbers
            convert the output to a JSON
            Specifications:

            Database Connection:

            Use the variable connectionString to connect to the PostgreSQL database.
            Exclude the line of code that defines the connectionString variable.
            Policy Data Query:

            table schema: wholesale_casualty_insurance_policies
            policy_id,company_name, policy_type, coverage_amount, premium, deductible, policy_start_date, policy_end_date, number_of_employees, industry, location, number_of_claims


            Here is the user question and the connectionString to use in the code:
            """,
        ),
        ("placeholder", "{messages}"),
        ("placeholder", "{connectionString}"),
    ]
    )

    llm = AzureChatOpenAI(
            openai_api_version=os.environ["AZURE_OPENAI_VERSION"],
            openai_api_key=os.environ["AZURE_OPENAI_KEY"],
            azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            temperature = 0.1
        )

    # Data model
    class code(BaseModel):
        """Code output"""
        prefix: str = Field(description="Description of the problem and approach")
        imports: str = Field(description="Code block import statements")
        code: List = Field(description="Code block not including import statements")

    question = name
    code_gen_chain = code_gen_prompt | llm.with_structured_output(code)

    code_result = code_gen_chain.invoke({"messages": [("user", question)]})
    code_to_execute = "connectionString="+f'"{connectionString}"'+ "\n" +code_result.imports + "\n" + "\n".join(code_result.code)

    print(code_to_execute)

    repl_result = repl.run(code_to_execute)

    parsed_result = json.loads(json.dumps(repl_result, indent=2))
    print(repl_result)
    print("################################################")
    print("LLM Generated code to get data from Policy Admin System:")
    print("################################################")
    # Access individual elements of the result
    print(code_to_execute)


    return f"{repl_result}"
