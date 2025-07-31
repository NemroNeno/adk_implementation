from tavily import TavilyClient
from twilio.rest import Client
from app.core.config import settings

def tavily_search(query: str) -> str:
    """Finds real-time information on the internet."""
    try:
        tavily = TavilyClient(api_key=settings.TAVILY_API_KEY)
        response = tavily.search(query=query, search_depth="basic")
        return "\n".join([f"Source: {obj['url']}\nContent: {obj['content']}" for obj in response['results'][:3]])
    except Exception as e:
        return f"Tavily search failed: {e}"

def send_sms(to_number: str, body: str) -> str:
    """Sends an SMS message to a specified phone number."""
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(body=body, from_=settings.TWILIO_PHONE_NUMBER, to=to_number)
        return f"SMS sent successfully. Message SID: {message.sid}"
    except Exception as e:
        return f"Failed to send SMS. Error: {str(e)}"