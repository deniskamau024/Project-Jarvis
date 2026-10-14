import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Force python to find the .env file
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, ".env")
load_dotenv(dotenv_path=env_path)

# 2. Initialize the OpenAI clientgi
client = OpenAI()

# 3. Define Denis's custom Jarvis Persona
JARVIS_SYSTEM_PROMPT = (
    "You are J.A.R.V.I.S., a highly intelligent, witty, and sophisticated AI assistant. "
    "You are assisting Mr. Denis from Kenya. You have access to an internet search tool."
    "Use it automatically whenever he asks for real-time information."
    "Be direct, helpful, and address him as Sir."

)

def run_jarvis():
    print("Initializing J.A.R.V.I.S. Core Protocols...")
    
    # This array keeps track of your conversation history so Jarvis has a memory
    conversation_history = [
        {"role": "system", "content": JARVIS_SYSTEM_PROMPT}
    ]
    
    print("\n[JARVIS]: Systems online. Good day, Mr. Denis. How may I help you today?")
    
    # Continuous interaction loop
    while True:
        try:
            # Capture your terminal input
            user_input = input("\n[Mr. Denis]: ")
            
            # Check for exit commands
            if user_input.lower().strip() in ["exit", "quit", "shutdown", "goodbye"]:
                print("\n[JARVIS]: Understood, Sir. Powering down subsystems. Goodbye.")
                break
                
            if not user_input.strip():
                continue
                
            # Add your message to his memory
            conversation_history.append({"role": "user", "content": user_input})
            
            # Send the conversation history to the OpenAI brain
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=conversation_history
            )
            
            # FIXED SYNTAX: Cleanly parse the response message text
            jarvis_reply = response.choices[0].message.content
            print(f"\n[JARVIS]: {jarvis_reply}")
            
            # Add Jarvis's reply to his memory so he remembers it on your next turn
            conversation_history.append({"role": "assistant", "content": jarvis_reply})
            
        except Exception as e:
            print(f"\nAn execution error occurred: {e}")
            break

if __name__ == "__main__":
    run_jarvis()