from langchain.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from twilio.rest import Client
from app.core.config import settings

class SendSmsInput(BaseModel):
    to_number: str = Field(description="The recipient's phone number in E.164 format (e.g., +15551234567).")
    body: str = Field(description="The content of the SMS message to send.")

class TwilioSmsTool(BaseTool):
    # --- THE FIX IS HERE: Add type hints (str) ---
    name: str = "send_sms"
    description: str = "Useful for sending an SMS message to a specified phone number."
    # --- END OF FIX ---
    
    args_schema: Type[BaseModel] = SendSmsInput

    def _run(self, to_number: str, body: str) -> str:
        """Use the tool."""
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                body=body,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=to_number
            )
            return f"SMS sent successfully to {to_number}. Message SID: {message.sid}"
        except Exception as e:
            # It's better to return a structured error
            return f"Error: Failed to send SMS. Details: {str(e)}"

    # It's good practice to also define an async version for LangChain
    async def _arun(self, to_number: str, body: str) -> str:
        """Use the tool asynchronously."""
        # For the twilio library, the sync and async calls are the same
        # A more complex tool might use an async http client here
        return self._run(to_number, body)