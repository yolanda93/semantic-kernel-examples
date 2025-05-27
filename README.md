# semantic-kernel-examples
Examples of implementation to create different AI agents capabilities using semantic-kernel 

## Pre-requisites
- Python 3.8 or higher
- Azure OpenAI subscription
- Semantic Kernel Python SDK
- OpenAI Python SDK


## Project Setup

### Create Azure OpenAI endpoint
- Create new resource AI Foundry and deploy an LLM model endpoint
- Create a .venv with the following:
```
AZURE_OPENAI_API_KEY=api_key
AZURE_OPENAI_API_ENDPOINT=endpoint_url
AZURE_OPENAI_API_VERSION=deployment_version
AZURE_OPENAI_API_DEPLOYMENT_NAME=your_deployment_name
```

### Create an venv and install necessary packages
```
python -m venv .venv

pip install openai
pip install semantic-kernel
pip install chainlit
```

## Usage

Simple agents (without ui)

```
python 00_initial_agent.py
```

Agents with chainlit Chat UI 

```
chainlit run 01_simple_chat_agent.py -w
```

## References
This project takes some reference examples from:
https://github.com/sphenry/agent_hack
