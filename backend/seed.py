import time
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

# Import the engine, session factory, and Base
from app.db.base import engine, SessionLocal, Base

# Import the model
from app.db.models import Tool


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def seed_initial_data(db: Session):
    print("Seeding initial data...")
    
    # Seed Tavily
    if not db.query(Tool).filter(Tool.function_name == "tavily_search").first():
        print("Creating Tavily Search tool...")
        db.add(Tool(
            name="Tavily Internet Search",
            description="A powerful search engine for finding real-time information.",
            function_name="tavily_search",
            is_public=True
        ))
        db.commit()
        print("Tavily Search tool created.")
    else:
        print("Tavily Search tool already exists.")
        
    # Seed Twilio
    if not db.query(Tool).filter(Tool.function_name == "send_sms").first():
        print("Creating Twilio SMS tool...")
        db.add(Tool(
            name="Send SMS (Twilio)",
            description="Allows the agent to send a text message.",
            function_name="send_sms",
            is_public=True
        ))
        db.commit()
        print("Twilio SMS tool created.")
    else:
        print("Twilio SMS tool already exists.")

# ... (rest of the file is the same) ...s


def main():
    print("Initializing database connection...")
    db_connected = False
    retries = 5

    while retries > 0 and not db_connected:
        try:
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

    db_session = get_db()
    db = next(db_session)
    try:
        seed_initial_data(db)
    finally:
        next(db_session, None)

    print("Database seeding process complete.")


if __name__ == "__main__":
    main()
