# This function is not intended to be invoked directly. Instead it will be
# triggered by an HTTP starter function.
# Before running this sample, please:
# - create a Durable activity function (default name is "Hello")
# - create a Durable HTTP starter function
# - add azure-functions-durable to requirements.txt
# - run pip install -r requirements.txt

import logging
import json

import azure.functions as func
import azure.durable_functions as df
from datetime import timedelta

def orchestrator_function(context: df.DurableOrchestrationContext):
    logging.info(f"Payload from HTTP Trigger: " + context.get_input() )
    input_data = context.get_input()
    parsed_data = json.loads(input_data)
    question = parsed_data.get('prompt')

    fetch_policy_data_agent_results = yield context.call_activity('fetch_policy_data_agent', question)
    print(fetch_policy_data_agent_results)
    check_internal_rules_for_risk_agent_results = yield context.call_activity('check_internal_rules_for_risk_agent', fetch_policy_data_agent_results)
    print(check_internal_rules_for_risk_agent_results)
    check_industry_risk_agent_results = yield context.call_activity('check_industry_risk_agent', check_internal_rules_for_risk_agent_results)
    print(check_industry_risk_agent_results)

    return [check_industry_risk_agent_results]

main = df.Orchestrator.create(orchestrator_function)