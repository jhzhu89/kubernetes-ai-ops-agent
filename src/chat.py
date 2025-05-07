import chainlit as cl
from agents import ItemHelpers, Runner
from openai.types.responses import ResponseTextDeltaEvent
from agents.exceptions import MaxTurnsExceeded
from chainlit_session_manager import ChainlitSessionManager
from chainlit_session_storage import ChainlitSessionStorage
from openai_client_factory_impl import OpenAIClientFactoryImpl

# Import the agent_provider initialized in main.py
from main import agent_provider

# Create dependencies
openai_client_factory = OpenAIClientFactoryImpl()
openai_client_factory.configure_defaults()

async def get_or_create_session_manager(user_session):
    """Creates or retrieves a ChainlitSessionManager for the current user session"""
    session_manager = user_session.get("session_manager")
    if session_manager:
        return session_manager

    session_storage = ChainlitSessionStorage(user_session)
    session_manager = ChainlitSessionManager(session_storage=session_storage)
    user_session.set("session_manager", session_manager)
    
    return session_manager


@cl.on_chat_start
async def on_chat_start():
    """Initialize session when a new chat starts"""
    await get_or_create_session_manager(cl.user_session)


@cl.on_message
async def on_message(message: cl.Message):
    """Process incoming messages using the agent"""
    session_manager = await get_or_create_session_manager(cl.user_session)
    
    # Extract message content and update history
    message_content = message.content
    message_history = session_manager.get_message_history()
    message_history.append({"role": "user", "content": message_content})
    
    try:
        msg = cl.Message(content="")

        # Run the agent with message history
        result = Runner.run_streamed(
            starting_agent=agent_provider.get_agent(),
            input=message_history,
            max_turns=10
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
                tool_name = event.item.raw_item.name
                tool_args = event.item.raw_item.arguments
                tool_call_id = event.item.raw_item.call_id
                
                # Create step for tool call
                async with cl.Step(
                    name=f"Tool: {tool_name}",
                    type="tool_call",
                    show_input=True
                ) as step:
                    step.input = tool_args
                    await step.send()
                
                # Store step with call_id in session
                tool_steps = session_manager.get_tool_steps()
                tool_steps[tool_call_id] = step
                session_manager.save_tool_steps(tool_steps)
                continue
                
            if event.item.type == "tool_call_output_item":
                tool_call_id = event.item.raw_item['call_id'] 

                # Retrieve corresponding step from session
                tool_steps = session_manager.get_tool_steps()
                step = tool_steps.get(tool_call_id)
                
                if step:
                    # Update step with output
                    step.output = event.item.output
                    await step.stream_token(event.item.output)
                    
                    # Release step after use
                    if tool_call_id in tool_steps:
                        del tool_steps[tool_call_id]
                        session_manager.save_tool_steps(tool_steps)
                        print(f"Released step for tool call ID: {tool_call_id}")
                continue                                                   

            if event.item.type == "message_output_item":
                output = ItemHelpers.text_message_output(event.item)
                message_history.append({"role": "assistant", "content": output})
                continue

        await msg.update()

    except MaxTurnsExceeded:
        await cl.Message(content="I've reached the maximum processing steps without finding a complete answer. Please try rephrasing your question.").send()
    except Exception as e:
        print(f"Exception type: {type(e).__name__}, Error: {str(e)}")
        await cl.Message(content=f"Error occurred: {str(e)}, Type: {type(e).__name__}").send()
    
    # Save updated message history
    session_manager.save_message_history(message_history)


@cl.on_chat_end
async def on_chat_end():
    """Clean up session resources when chat ends"""
    session_manager = cl.user_session.get("session_manager")
    if session_manager:
        await session_manager.cleanup()
        cl.user_session.set("session_manager", None)