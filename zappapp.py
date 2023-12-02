from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import openai
from dotenv import load_dotenv, find_dotenv
import os
import time

# Load environment variables with improved method
load_dotenv(find_dotenv())

app = Flask(__name__)

# Retrieve environment variables
openai.api_key = os.getenv('OPENAI_API_KEY')

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    body = request.values.get('Body', None)
    assistant_response = get_assistant_response(body)

    # Create a Twilio Messaging Response
    response = MessagingResponse()
    
    # Ensure the assistant response is a string
    if isinstance(assistant_response, list):
        assistant_response = ''.join(assistant_response)  # Convert list to string if needed
    elif not isinstance(assistant_response, str):
        assistant_response = "An error occurred."

    response.message(assistant_response)
    return str(response)

def get_assistant_response(user_message):
    try:
        # Initialize the client
        client = openai.OpenAI(api_key=openai.api_key)

        # Step 1: Create an Assistant using the beta namespace
        assistant = client.beta.assistants.create(
            name="Math Tutor",
            instructions="You are a personal math tutor. Write and run code to answer math questions.",
            tools=[{"type": "code_interpreter"}],
            model="gpt-4-1106-preview"
        )

        # Step 2: Create a Thread using the beta namespace without the assistant_id
        thread = client.beta.threads.create()

        # Step 3: Add a Message to a Thread using the beta namespace
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_message
        )

        # Step 4: Run the Assistant using the beta namespace
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
        )

        # Blocking call to wait for the run to complete; not recommended for production environments
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == 'completed':
                break
            time.sleep(0.5)  # Adjust the timing as needed for your use case

        # Retrieve all messages from the thread using the beta namespace
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        assistant_messages = [msg.content for msg in messages.data if msg.role == 'assistant']

        # Return the latest assistant message
        return ''.join(assistant_messages[-1]) if assistant_messages else "No response from the assistant."

    except Exception as e:
        print(f"An error occurred: {e}")
        return "I am unable to process your request at the moment."

if __name__ == "__main__":
    app.run(debug=True)
