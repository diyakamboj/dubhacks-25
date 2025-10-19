# gemini_pipeline.py
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

try:
    from google import genai
    client = genai.Client(api_key=api_key)
except ImportError:
    print("❌ 'google-genai' library not installed.")
    client = None

if not api_key:
    print("❌ Gemini API key not found!")
else:
    print("✅ Gemini API key loaded successfully!")

# Emergency context storage
emergency_context = None
conversation_memory = []

def start_emergency_guidance(emergency_type):
    """Called by your ML model when emergency detected"""
    global emergency_context, conversation_memory
    
    emergency_context = {
        "type": emergency_type,
        "current_step": 1,
        "steps_given": [],
        "user_questions": []
    }
    
    conversation_memory = [f"Emergency detected: {emergency_type}"]
    
    # Get first instruction from Gemini
    prompt = f"""
    Start first aid instructions for {emergency_type}. 
    Give ONLY the first immediate step. Keep it under 2 sentences.
    """
    
    first_step = get_gemini_response(prompt)
    conversation_memory.append(f"Gemini: {first_step}")
    
    return {
        "intent": "emergency_started",
        "emergency_type": emergency_type, 
        "response": first_step,
        "instruction": "Ask questions or say 'next' for next step"
    }

def process_user_response(user_text):
    """Process user questions/responses during emergency"""
    global emergency_context, conversation_memory
    
    if not emergency_context:
        return {"intent": "no_emergency", "response": "No active emergency"}
    
    # Add user message to memory
    conversation_memory.append(f"User: {user_text}")
    
    # Build context for Gemini
    recent_context = "\n".join(conversation_memory[-6:])
    
    prompt = f"""
    Emergency Context: {emergency_context['type']}
    Conversation History: {recent_context}
    
    User just said: "{user_text}"
    
    Your role: Provide the next appropriate first aid guidance.
    Keep responses under 3 sentences, practical and clear.
    Respond with the next instruction or answer:
    """
    
    gemini_response = get_gemini_response(prompt)
    
    # Update context and memory
    conversation_memory.append(f"Gemini: {gemini_response}")
    emergency_context["steps_given"].append(gemini_response)
    
    return {
        "intent": "emergency_guidance",
        "emergency_type": emergency_context["type"],
        "response": gemini_response
    }

def get_gemini_response(prompt):
    if not client:
        return "Please continue with emergency first aid procedures."
    
    try:
        response = client.models.generate_content(
            model='models/gemini-2.0-flash',
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return "Please continue with the emergency procedure."

# REMOVED THE SELF-IMPORT - that was causing the error