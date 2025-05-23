import chainlit as cl
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.skill_definition import read_skill_from_directory
from semantic_kernel.connectors.ai.azure_open_ai import AzureChatCompletion
import os

# Initialize Semantic Kernel once
kernel = Kernel()
kernel.add_text_completion_service(
    "openai", OpenAIChatCompletion("gpt-4", api_key="your-openai-api-key")
)
welcome_skill = read_skill_from_directory("skills", "WelcomeSkill")
generate_welcome = welcome_skill["generate_welcome_message"]

# Store session state
user_state = {}


@cl.on_chat_start
async def on_chat_start():
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
    user_state["step"] = "ask_name"

@cl.on_message
async def on_message(message: cl.Message):
    step = user_state.get("step")

    if step == "ask_name":
        user_state["name"] = message.content.strip()
        user_state["step"] = "ask_company"
        await cl.Message(content=f"Great, {user_state['name']}! What's the name of your company?").send()

    elif step == "ask_company":
        user_state["company"] = message.content.strip()
        user_state["step"] = "complete"

        # Call Semantic Kernel
        context = {
            "name": user_state["name"],
            "company": user_state["company"]
        }
        welcome_msg = await kernel.run_async(generate_welcome, input_context=context)

        await cl.Message(content=str(welcome_msg)).send()
        await cl.Message(content="Thanks! You're all set.").send()
    else:
        await cl.Message(content="You're already onboarded.").send()
