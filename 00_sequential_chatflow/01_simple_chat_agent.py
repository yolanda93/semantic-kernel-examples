import os
import chainlit as cl
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from dotenv import load_dotenv
from semantic_kernel.agents import ChatCompletionAgent

# Load environment variables
if os.path.exists('../.env'):
    load_dotenv(dotenv_path='../.env')
elif os.path.exists('.env'):
    load_dotenv(dotenv_path='.env')
else:
    print("Warning: .env file not found. Please ensure Azure OpenAI credentials are set.")

# Store session state
user_state = {}

# Initialize Semantic Kernel once
@cl.on_chat_start
async def on_chat_start():
    kernel = sk.Kernel()
    try:
        ai_service = AzureChatCompletion(
            deployment_name=os.getenv("AZURE_OPENAI_API_DEPLOYMENT_NAME"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            endpoint=os.getenv("AZURE_OPENAI_API_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION")
        )
        kernel.add_service(ai_service)
    except Exception as e:
        await cl.Message(content=f"Error initializing AI service: {e}").send()
        return

    await cl.Message(content="Hi! Welcome to Acme Software. Let's get you onboarded.").send()
    await cl.Message(content="What’s your name?").send()
    user_state["next_step"] = "ask_company"

@cl.on_message
async def on_message(message: cl.Message):
    next_step = user_state.get("next_step")

    if next_step == "ask_company":
        user_state["name"] = message.content.strip()
        await cl.Message(content=f"Great, {user_state['name']}! What's the name of your company?").send()
        user_state["next_step"] = "complete"

    elif next_step == "complete":
        user_state["company"] = message.content.strip()
        user_state["next_step"] = "finshed"

        # Call Semantic Kernel
        context = {
            "name": user_state["name"],
            "company": user_state["company"]
        }
        await cl.Message(content=f"Welcome, {user_state['company']}! ").send()
        await cl.Message(content="Thanks! You're all set.").send()
    else:
        await cl.Message(content="You're already onboarded.").send()
