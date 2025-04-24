import chainlit as cl
from agents import ItemHelpers, Runner
from openai.types.responses import ResponseTextDeltaEvent
from agents.exceptions import MaxTurnsExceeded
from chainlit_session_manager import ChainlitSessionManager
from chainlit_session_storage import ChainlitSessionStorage
from openai_client_factory_impl import OpenAIClientFactoryImpl
from kubernetes_ai_ops_agent_provider import KubernetesAIOpsAgentProvider
import asyncio
import atexit
import signal

# Create dependencies
openai_client_factory = OpenAIClientFactoryImpl()
openai_client_factory.configure_defaults()

# Create application-level agent context and agent
# These will be shared across all user sessions
agent_provider = KubernetesAIOpsAgentProvider()

# Initialize the agent when the application starts
loop = asyncio.get_event_loop()
loop.run_until_complete(agent_provider.initialize())

# Register cleanup handlers for application shutdown
atexit.register(lambda: loop.run_until_complete(agent_provider.cleanup()))
# Register signal handlers
for sig in [signal.SIGINT, signal.SIGTERM]:
    signal.signal(sig, lambda signum, frame: loop.run_until_complete(agent_provider.cleanup()))

async def get_or_create_session_manager(user_session):
    """
    Creates a new ChainlitSessionManager instance.
    
    Args:
        user_session: Chainlit user session object
        
    Returns:
        A ChainlitSessionManager instance ready to use
    """
    session_manager = user_session.get("session_manager")
    if session_manager:
        return session_manager

    # Create the session storage adapter
    session_storage = ChainlitSessionStorage(user_session)
    
    session_manager = ChainlitSessionManager(session_storage=session_storage)
    
    # Store in user session for later retrieval
    user_session.set("session_manager", session_manager)
    
    return session_manager


@cl.on_chat_start
async def on_chat_start():
    """
    Callback triggered when a new chat/session is started.
    Initialize the session with all required resources.
    """
    # Create the session manager
    await get_or_create_session_manager(cl.user_session)


@cl.on_message
async def on_message(message: cl.Message):
    """
    Callback that handles incoming messages.
    It retrieves the agent from the session and uses it to process the query.
    """
    session_manager = await get_or_create_session_manager(cl.user_session)
    
    # Extract the message content
    message_content = message.content
    
    # Get the message history, add the current user message
    message_history = session_manager.get_message_history()
    message_history.append({"role": "user", "content": message_content})
    
    try:
        msg = cl.Message(content="")

        # Use message history as input with the application-level agent
        result = Runner.run_streamed(
            starting_agent=agent_provider.get_agent(),  # Use the getter method to access the agent
            input=message_history,
            max_turns=10  # Limit the number of turns
        )
        
        async for event in result.stream_events():
            if event.type == "raw_response_event":
                if isinstance(event.data, ResponseTextDeltaEvent):
                    await msg.stream_token(event.data.delta)
                continue

            if event.type == "agent_updated_stream_event":
                continue

            if event.item.type == "tool_call_item":
                print("-- Tool was called")
                # Tool call items have a raw_item attribute that contains the actual tool call data
                tool_name = event.item.raw_item.name
                tool_args = event.item.raw_item.arguments
                tool_call_id = event.item.raw_item.call_id
                
                # Create a step for the tool call and store it in the session
                async with cl.Step(
                    name=f"Tool: {tool_name}",
                    type="tool_call",
                    show_input=True
                ) as step:
                    step.input = tool_args
                    await step.send()
                
                # Store the step with the call_id in the session
                tool_steps = session_manager.get_tool_steps()
                tool_steps[tool_call_id] = step
                session_manager.save_tool_steps(tool_steps)
                continue
                
            if event.item.type == "tool_call_output_item":
                tool_call_id = event.item.raw_item['call_id'] 

                # Retrieve the corresponding step from the session
                tool_steps = session_manager.get_tool_steps()
                step = tool_steps.get(tool_call_id)
                
                if step:
                    # Update the step with the output
                    step.output = event.item.output
                    await step.stream_token(event.item.output)
                    
                    # Release the step after use by removing it from the dictionary
                    if tool_call_id in tool_steps:
                        del tool_steps[tool_call_id]
                        session_manager.save_tool_steps(tool_steps)
                        print(f"Released step for tool call ID: {tool_call_id}")
                continue                                                   

            if event.item.type == "message_output_item":
                output = ItemHelpers.text_message_output(event.item)
                message_history.append({"role": "assistant", "content": output})
                continue

            # Ignore other event types
            pass

        await msg.update()

    except MaxTurnsExceeded:
        await cl.Message(content="I reached the maximum number of processing steps without finding a complete answer. Please try rephrasing your question.").send()
        # TODO: handle tool call exceptions.
    except Exception as e:
        print(f"Exception type: {type(e).__name__}, Error: {str(e)}")
        
        await cl.Message(content=f"An error occurred: {str(e)}, Exception type: {type(e).__name__}").send()
    
    # Save the updated message history to the session
    session_manager.save_message_history(message_history)


@cl.on_chat_end
async def on_chat_end():
    """
    Callback triggered when a chat/session ends.
    Clean up session resources but keep the application-level agent.
    """
    session_manager = cl.user_session.get("session_manager")
    if session_manager:
        # Clean up the session manager resources without closing the agent context
        await session_manager.cleanup()
        cl.user_session.set("session_manager", None)