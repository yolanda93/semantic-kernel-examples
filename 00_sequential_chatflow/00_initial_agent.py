import os
from dotenv import load_dotenv
import asyncio
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

# Load environment variables
if os.path.exists('../.env'):
    load_dotenv(dotenv_path='../.env')
elif os.path.exists('.env'):
    load_dotenv(dotenv_path='.env')
else:
    print("Warning: .env file not found. Please ensure Azure OpenAI credentials are set.")


async def main():
    # Initialize a chat agent with basic instructions
    agent = ChatCompletionAgent(
        service = AzureChatCompletion(
            deployment_name=os.getenv("AZURE_OPENAI_API_DEPLOYMENT_NAME"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            endpoint=os.getenv("AZURE_OPENAI_API_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION")
        ),
        name="SK-Assistant",
        instructions="You are a helpful assistant.",
    )

    # Get a response to a user message
    response = await agent.get_response(messages="Write a haiku about Semantic Kernel.")
    print(response.content)

asyncio.run(main()) 

# Output:
# Language's essence,
# Semantic threads intertwine,
# Meaning's core revealed.