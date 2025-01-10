# This function is not intended to be invoked directly. Instead it will be
# triggered by an orchestrator function.
# Before running this sample, please:
# - create a Durable orchestration function
# - create a Durable HTTP starter function
# - add azure-functions-durable to requirements.txt
# - run pip install -r requirements.txt


import logging
import json
import os
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_openai import AzureChatOpenAI

AZURE_OPENAI_KEY = os.environ["AZURE_OPENAI_KEY"] 
AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"] 
AZURE_OPENAI_DEPLOYMENT = os.environ["AZURE_OPENAI_DEPLOYMENT"] 
AZURE_OPENAI_VERSION = os.environ["AZURE_OPENAI_VERSION"] 
AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT = os.environ["AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT"] 

# Data model
# Data model
class PolicyScreeningDecision(BaseModel):
    decesion: str = Field(description="the decesion of the policy screening, it can be either 'approve', 'reject' or 'review'")
    reason: str = Field(description="The for the policy screening decesion")

llm = AzureChatOpenAI(
        openai_api_version=os.environ["AZURE_OPENAI_VERSION"],
        openai_api_key=os.environ["AZURE_OPENAI_KEY"],
        azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"]
    )

structured_llm_router = llm.with_structured_output(PolicyScreeningDecision)

# Prompt 
system = """You are an policy rewiew expert, your task is access risk associated with each insurance policy and make a decesion to approve, reject or review. 
here are rules to follow:
if policies have relatively moderate claims (less than 2) histories and/or are in industries with manageable risk profiles, then decesion should be approve , and provide reason for decesion.
if Policies have very high claims ( greater then 5) that present significant risk without acceptable adjustments,then decesion should be review , and provide reason for decesion.
if Policies have moderate claims (more than 2 less than 5) histories and/or are in industries with manageable risk profiles, then decesion should be review, and provide reason for decesion.
"""

policy_screening_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "{question}"),
    ]
)

policy_screening = policy_screening_prompt | structured_llm_router
#print(policy_screening.invoke({"question": "Who will the Bears draft first in the NFL draft?"}))

def main(name: str) -> str:
    #print(name)
    policies = json.loads(name)
    response = policy_screening.invoke({"question": "analyze the risk associated with the policy : " + str(policies) })

    print("################################################")
    print("Processing policy...")
    print("################################################")

    print("################################################")
    print("Done processing policy, here are the results:")
    print("################################################")
    print(json.dumps({
        "policy": policies,
        "decision": response.decesion,
        "reason": response.reason
    }))
    print("################################################")

    return json.dumps({
        "policy": policies,
        "decision": response.decesion,
        "reason": response.reason
    })