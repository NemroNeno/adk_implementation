from google_adk.tools import tool
from tavily import TavilyClient
from twilio.rest import Client
from app.core.config import settings

@tool
def tavily_search(query: str) -> str:
    """
    Finds real-time information on the internet using the Tavily search engine.
    Use this for any questions about recent events, news, or specific, factual topics.
    Args:
        query (str): The search query.
    """
    try:
        tavily = TavilyClient(api_key=settings.TAVILY_API_KEY)
        response = tavily.search(query=query, search_depth="basic")
        return "\n".join([f"Source: {obj['url']}\nContent: {obj['content']}" for obj in response['results'][:3]])
    except Exception as e:
        return f"Tavily search failed: {e}"

@tool
def send_sms(to_number: str, body: str) -> str:
    """
    Sends an SMS message to a specified phone number.
    Args:
        to_number (str): The recipient's phone number in E.164 format (e.g., +15551234567).
        body (str): The content of the SMS message to send.
    """
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=to_number
        )
        return f"SMS sent successfully. Message SID: {message.sid}"
    except Exception as e:
        return f"Failed to send SMS. Error: {str(e)}"

# A dictionary to easily access our ADK-defined tools
ADK_TOOL_REGISTRY = {
    "tavily_search": tavily_search,
    "send_sms": send_sms,
}