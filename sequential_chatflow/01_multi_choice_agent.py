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

# Define conversation states
STATE_INITIAL = "INITIAL"
STATE_INTERNET_ASK_RESTART = "INTERNET_ASK_RESTART"
STATE_INTERNET_RESTARTED_YES = "INTERNET_RESTARTED_YES"
STATE_INTERNET_RESTARTED_NO = "INTERNET_RESTARTED_NO"
STATE_SOFTWARE_ASK_NAME = "SOFTWARE_ASK_NAME"
STATE_SOFTWARE_ASK_PROBLEM = "SOFTWARE_ASK_PROBLEM"
STATE_HARDWARE_ASK_SYMPTOMS = "HARDWARE_ASK_SYMPTOMS"
STATE_FINAL = "FINAL"

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

    # Agent instructions are minimal as the flow is mostly scripted
    agent_instructions = "You are a friendly and helpful Tech Support Bot. Follow the conversational flow provided by the system."
    agent = ChatCompletionAgent(kernel=kernel, name="TechSupportBot", instructions=agent_instructions)

    cl.user_session.set("agent", agent)
    cl.user_session.set("conversation_state", STATE_INITIAL)
    cl.user_session.set("cl_history", [])
    # Store the agent for use in action callbacks if needed
    cl.user_session.set("tech_support_agent", agent)


    initial_actions = [
        cl.Action(name="internet_issue", value="Internet Issue", label="Internet Issue", payload={"value": "Internet Issue"}),
        cl.Action(name="software_problem", value="Software Problem", label="Software Problem", payload={"value": "Software Problem"}),
        cl.Action(name="hardware_failure", value="Hardware Failure", label="Hardware Failure", payload={"value": "Hardware Failure"}),
    ]
    await cl.Message(
        content="Welcome to Tech Support! How can I help you today? Please choose an option:",
        actions=initial_actions,
        author=agent.name
    ).send()

async def send_response_after_action(
    triggering_action: cl.Action,
    response_content: str,
    new_actions_to_present: list[cl.Action],
    next_state: str,
    author_name: str = "TechSupportBot"
):
    """Helper function to log user action, send message, update history and state."""
    cl_history: list = cl.user_session.get("cl_history", [])

    # Log the action the user just took, using the label for readability
    cl_history.append({"role": "user", "content": f"Action: {triggering_action.label}"})

    # Send the bot's response message with new actions
    await cl.Message(content=response_content, actions=new_actions_to_present, author=author_name).send()

    # Log the assistant's response
    cl_history.append({"role": "assistant", "content": response_content})

    # Update history and state in the session
    cl.user_session.set("cl_history", cl_history)
    cl.user_session.set("conversation_state", next_state)

@cl.action_callback("internet_issue")
async def on_action_internet_issue(action: cl.Action):
    agent: ChatCompletionAgent = cl.user_session.get("tech_support_agent")
    response_content = "Okay, for Internet Issues, have you tried restarting your modem and router?"
    new_actions = [
        cl.Action(name="internet_restarted_yes", value="Yes", label="Yes, I tried", payload={"value": "Yes"}),
        cl.Action(name="internet_restarted_no", value="No", label="No, I haven't", payload={"value": "No"}),
    ]
    await send_response_after_action(action, response_content, new_actions, STATE_INTERNET_ASK_RESTART, agent.name)

@cl.action_callback("software_problem")
async def on_action_software_problem(action: cl.Action):
    agent: ChatCompletionAgent = cl.user_session.get("tech_support_agent")
    response_content = "For Software Problems, which software are you having trouble with? Please type the name."
    await send_response_after_action(action, response_content, [], STATE_SOFTWARE_ASK_NAME, agent.name)

@cl.action_callback("hardware_failure")
async def on_action_hardware_failure(action: cl.Action):
    agent: ChatCompletionAgent = cl.user_session.get("tech_support_agent")
    response_content = "I'm sorry to hear you're having a hardware failure. To help us diagnose it, please describe the symptoms you're observing."
    await send_response_after_action(action, response_content, [], STATE_HARDWARE_ASK_SYMPTOMS, agent.name)

@cl.action_callback("internet_restarted_yes")
async def on_action_internet_restarted_yes(action: cl.Action):
    agent: ChatCompletionAgent = cl.user_session.get("tech_support_agent")
    response_content = "Got it. Could you please describe the issue in more detail? For example, are websites loading slowly, or are you completely disconnected?"
    await send_response_after_action(action, response_content, [], STATE_INTERNET_RESTARTED_YES, agent.name)

@cl.action_callback("internet_restarted_no")
async def on_action_internet_restarted_no(action: cl.Action):
    agent: ChatCompletionAgent = cl.user_session.get("tech_support_agent")
    response_content = "Please try restarting your modem and router first. This often resolves common connectivity issues. Let me know if that helps!"
    await send_response_after_action(action, response_content, [], STATE_INTERNET_RESTARTED_NO, agent.name)


@cl.action_callback("start_over")
async def on_action_start_over(action: cl.Action): # 'action' is the "start_over" action
    agent: ChatCompletionAgent = cl.user_session.get("tech_support_agent")
    response_content = "Welcome back to Tech Support! How can I help you today? Please choose an option:"
    new_actions = [
        cl.Action(name="internet_issue", value="Internet Issue", label="Internet Issue", payload={"value": "Internet Issue"}),
        cl.Action(name="software_problem", value="Software Problem", label="Software Problem", payload={"value": "Software Problem"}),
        cl.Action(name="hardware_failure", value="Hardware Failure", label="Hardware Failure", payload={"value": "Hardware Failure"}),
    ]
    # The helper will log "Action: Start Over" (using action.label)
    # and then send the response_content with new_actions.
    # It will also set the state to STATE_INITIAL.
    await send_response_after_action(action, response_content, new_actions, STATE_INITIAL, agent.name)


@cl.on_message
async def on_message(message: cl.Message):
    agent: ChatCompletionAgent = cl.user_session.get("agent") # or "tech_support_agent"
    state: str = cl.user_session.get("conversation_state")
    cl_history: list = cl.user_session.get("cl_history", [])

    if not agent:
        await cl.Message(content="Agent not initialized. Please restart chat.").send()
        return

    user_input = message.content
    cl_history.append({"role": "user", "content": str(user_input)})

    response_content = ""
    actions = []
    next_state = state
    send_standard_response = True


    if state == STATE_INITIAL:
        # This state should ideally be handled by action callbacks.
        # If user types something unexpected here.
        response_content = "Sorry, I didn\'t understand that. Please choose one of the options above."
        actions = [
            cl.Action(name="internet_issue", value="Internet Issue", label="Internet Issue", payload={"value": "Internet Issue"}),
            cl.Action(name="software_problem", value="Software Problem", label="Software Problem", payload={"value": "Software Problem"}),
            cl.Action(name="hardware_failure", value="Hardware Failure", label="Hardware Failure", payload={"value": "Hardware Failure"}),
        ]
        next_state = STATE_INITIAL

    elif state == STATE_INTERNET_ASK_RESTART:
        # This state is now primarily handled by internet_restarted_yes/no actions
        # If user types something instead of clicking Yes/No
        response_content = "Please select \'Yes\' or \'No\' using the buttons."
        actions = [
            cl.Action(name="internet_restarted_yes", value="Yes", label="Yes, I tried", payload={"value": "Yes"}),
            cl.Action(name="internet_restarted_no", value="No", label="No, I haven\'t", payload={"value": "No"}),
        ]
        next_state = STATE_INTERNET_ASK_RESTART

    elif state == STATE_INTERNET_RESTARTED_YES: # User describes the issue
        response_content = f"Thank you for the details about your internet issue: \'{user_input}\'. We\'ll look into it. Is there anything else I can help with today?"
        next_state = STATE_FINAL
        actions = [cl.Action(name="start_over", value="Start Over", label="Start Over", payload={"value": "Start Over"})]

    elif state == STATE_INTERNET_RESTARTED_NO: # User confirms if they restarted or describes issue
        # This state might need refinement based on what user types after being told to restart.
        # For now, assume they are providing more details or confirming restart.
        response_content = f"Okay, you mentioned: \'{user_input}\'. If restarting didn\'t help or you have other concerns, let me know. Otherwise, is there anything else?"
        next_state = STATE_FINAL
        actions = [cl.Action(name="start_over", value="Start Over", label="Start Over", payload={"value": "Start Over"})]

    elif state == STATE_SOFTWARE_ASK_NAME:
        cl.user_session.set("software_name", user_input) # Store software name
        response_content = f"Okay, and what specific problem are you experiencing with {user_input}?"
        next_state = STATE_SOFTWARE_ASK_PROBLEM

    elif state == STATE_SOFTWARE_ASK_PROBLEM:
        software_name = cl.user_session.get("software_name", "the software")
        response_content = f"Thanks for explaining the issue with {software_name}: '{user_input}'. We'll investigate this. Can I help with anything else?"
        next_state = STATE_FINAL
        actions = [cl.Action(name="start_over", value="Start Over", label="Start Over", payload={"value": "Start Over"})]

    elif state == STATE_HARDWARE_ASK_SYMPTOMS:
        response_content = f"Thank you for describing the hardware symptoms: '{user_input}'. A specialist will review this. Is there further assistance you need?"
        next_state = STATE_FINAL
        actions = [cl.Action(name="start_over", value="Start Over", label="Start Over", payload={"value": "Start Over"})]
    
    elif state == STATE_FINAL:
        if user_input.lower() == "start over": # Handle typed "start over"
            await on_action_start_over(cl.Action(name="start_over", value="Start Over", label="Start Over"))
            send_standard_response = False # on_action_start_over handles its own response
        else:
            # Use LLM for generic follow-up
            send_standard_response = False # LLM part will send its own message
            response_msg_llm = cl.Message(content="", author=agent.name)
            full_llm_response = ""
            # Ensure thread is initialized for LLM interaction if not already
            thread_id = cl.user_session.get("thread_id") 
            if not thread_id:
                # Create a new thread if one doesn't exist.
                # This part depends on how your ChatCompletionAgent handles threads.
                # For simplicity, let's assume invoke_stream can handle a None thread or creates one.
                # Or, you might need to create/get a thread_id explicitly here.
                # For now, we'll pass what we have.
                pass


            async for chunk in agent.invoke_stream(user_input=user_input, thread_id=thread_id): # Pass thread_id
                if hasattr(chunk, 'content') and chunk.content:
                    await response_msg_llm.stream_token(chunk.content)
                    full_llm_response += chunk.content
                # Update thread_id if the agent provides it
                if hasattr(chunk, 'thread_id') and chunk.thread_id:
                     cl.user_session.set("thread_id", chunk.thread_id)
                elif hasattr(chunk, 'thread') and hasattr(chunk.thread, 'id'): # Alternative way thread might be passed
                     cl.user_session.set("thread_id", chunk.thread.id)

            if response_msg_llm.streaming:
                await response_msg_llm.send()
            elif full_llm_response:
                response_msg_llm.content = full_llm_response
                await response_msg_llm.send()
            else:
                await cl.Message(content="Is there anything specific I can help you with regarding that?", author=agent.name).send()
            
            cl_history.append({"role": "assistant", "content": full_llm_response or "Is there anything specific I can help you with regarding that?"})
            cl.user_session.set("cl_history", cl_history)
            # STATE_FINAL remains STATE_FINAL unless "Start Over"
            cl.user_session.set("conversation_state", STATE_FINAL)


    if send_standard_response:
        await cl.Message(content=response_content, actions=actions, author=agent.name).send()
        cl_history.append({"role": "assistant", "content": response_content})
        cl.user_session.set("conversation_state", next_state)
    
    cl.user_session.set("cl_history", cl_history)

# To run: chainlit run examples/13_multi_choice_agent.py -w
