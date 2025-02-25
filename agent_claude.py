"""
Telegram AI Agent using LangGraph, telebot and OpenAI with context memory

This script creates an AI agent that:
1. Connects to Telegram Bot API
2. Receives messages from users
3. Processes them using OpenAI with conversation context
4. Returns responses back to users
5. Uses LangGraph for potential future extensions
"""

import os
import telebot
from openai import OpenAI
from langgraph.graph import StateGraph
from dotenv import load_dotenv
from typing import TypedDict, Dict, Any, List

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE_URL = os.getenv("OPENAI_API_BASE_URL")
OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialize the Telegram Bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE_URL)

# Dictionary to store conversation history for each user
conversation_history: Dict[int, List[Dict[str, str]]] = {}

# Define state type for our graph
class AgentState(TypedDict):
    user_input: str
    agent_response: str
    user_id: int
    context: Dict[str, Any]
    messages: List[Dict[str, str]]

# Function to get conversation history for a user
def get_user_history(user_id: int) -> List[Dict[str, str]]:
    """Get conversation history for a specific user"""
    if user_id not in conversation_history:
        # Initialize with system message if this is a new user
        conversation_history[user_id] = [
            {"role": "system", "content": "You are a helpful assistant. Maintain a natural conversational style."}
        ]
    return conversation_history[user_id]

# Define nodes for our LangGraph
def process_with_openai(state: AgentState) -> AgentState:
    """Process user input with OpenAI API using conversation history"""
    user_id = state["user_id"]
    
    # Get existing conversation history
    messages = get_user_history(user_id)
    
    # Add the new user message to history
    messages.append({"role": "user", "content": state["user_input"]})
    
    try:
        # Send the entire conversation history to OpenAI
        response = openai_client.chat.completions.create(
            model=OPENAI_API_MODEL,
            messages=messages
        )
        
        # Get the assistant's response
        assistant_message = response.choices[0].message.content
        
        # Store the assistant's response in state
        state["agent_response"] = assistant_message
        
        # Add the assistant's response to the conversation history
        messages.append({"role": "assistant", "content": assistant_message})
        
        # Update the conversation history for this user
        conversation_history[user_id] = messages
        
        # Store the current messages in the state
        state["messages"] = messages
        
    except Exception as e:
        error_message = f"Error processing your request: {str(e)}"
        state["agent_response"] = error_message
        
        # Add error as system message to history
        messages.append({"role": "system", "content": f"Error occurred: {str(e)}"})
    
    return state

# Function to clear conversation history
def clear_history(state: AgentState) -> AgentState:
    """Clear conversation history for a user"""
    user_id = state["user_id"]
    
    # Reset conversation history to just the system message
    conversation_history[user_id] = [
        {"role": "system", "content": "You are a helpful assistant. Maintain a natural conversational style."}
    ]
    
    state["agent_response"] = "Conversation history has been cleared."
    state["messages"] = conversation_history[user_id]
    
    return state

# Create a LangGraph for our agent
def create_agent_graph():
    """Create the graph for our agent"""
    workflow = StateGraph(AgentState)
    
    # Define the nodes
    workflow.add_node("process_input", process_with_openai)
    workflow.add_node("clear_history", clear_history)
    
    # Define the conditional routing
    def should_clear_history(state: AgentState) -> str:
        # Check if message is a command to clear history
        if state["user_input"].lower() in ["/clear", "/reset", "clear context", "reset context"]:
            return "clear_history"
        return "process_input"
    
    # Define the edges with conditional routing
    workflow.add_conditional_edges(
        "",
        should_clear_history,
        {
            "process_input": "process_input",
            "clear_history": "clear_history"
        }
    )
    
    # Define the entry point
    workflow.set_entry_point("")
    
    # Compile the graph
    return workflow.compile()

# Create our agent graph
agent_graph = create_agent_graph()

# Handle incoming messages
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Handle incoming Telegram messages"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_input = message.text
    
    # Let user know the agent is processing
    bot.send_message(chat_id, "Processing your request...")
    
    # Initialize state with user input and user ID
    initial_state: AgentState = {
        "user_input": user_input,
        "agent_response": "",
        "user_id": user_id,
        "context": {},
        "messages": get_user_history(user_id)
    }
    
    # Run the graph
    final_state = agent_graph.invoke(initial_state)
    
    # Send the response back to the user
    bot.send_message(chat_id, final_state["agent_response"])

# Extension point: Add tools function
def add_tool(name, function):
    """Function to add new tools to the agent (for future extension)"""
    # This is a placeholder for future implementation
    # We'll expand this function when we need to add new tools
    pass

if __name__ == "__main__":
    print("Starting Telegram AI Agent with context memory...")
    try:
        # Start the bot
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Error during bot execution: {e}")
