import time
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

# We need to import the engine and session factory directly
from app.db.base import engine, SessionLocal, Base
# Import the specific model and schema we need
from app.db.models import Tool
from app.schemas.tool import ToolCreate

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def seed_initial_data(db: Session):
    print("Seeding initial data...")
    
    # --- Seed Tavily Tool ---
    tavily_tool = db.query(Tool).filter(Tool.langchain_key == "tavily_search").first()
    if not tavily_tool:
        print("Creating Tavily Search tool...")
        tool_in = Tool(
            name="Tavily Internet Search",
            description="A powerful search engine optimized for AI agents to find real-time information on the internet.",
            langchain_key="tavily_search",
            is_public=True
        )
        db.add(tool_in)
        db.commit()
        print("Tavily Search tool created and committed.")
    else:
        print("Tavily Search tool already exists.")

    # --- Seed Twilio SMS Tool ---
    twilio_tool = db.query(Tool).filter(Tool.langchain_key == "send_sms").first()
    if not twilio_tool:
        print("Creating Twilio SMS tool...")
        tool_in = Tool(
            name="Send SMS (Twilio)",
            description="Allows the agent to send a text message to a phone number.",
            langchain_key="send_sms",
            is_public=True
        )
        db.add(tool_in)
        db.commit()
        print("Twilio SMS tool created.")
    else:
        print("Twilio SMS tool already exists.")

def main():
    print("Initializing database connection...")
    db_connected = False
    retries = 5
    while retries > 0 and not db_connected:
        try:
            # Try to connect to the database
            connection = engine.connect()
            connection.close()
            print("Database connection successful.")
            db_connected = True
        except OperationalError:
            print(f"Database connection failed. Retrying in 5 seconds... ({retries} retries left)")
            retries -= 1
            time.sleep(5)
    
    if not db_connected:
        print("Could not connect to the database after several retries. Aborting.")
        return

    print("Creating database tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
    print("Tables created (if not already present).")

    db_session_gen = get_db()
    db = next(db_session_gen)
    try:
        seed_initial_data(db)
    finally:
        next(db_session_gen, None)
    
    print("Database seeding process complete.")

if __name__ == "__main__":
    main()
