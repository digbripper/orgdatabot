import os
from dotenv import load_dotenv
from langchain.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain.chat_models import ChatOpenAI

# Load environment variables
load_dotenv()

# Get credentials
db_uri = os.getenv("SUPABASE_DB_URL")
openai_key = os.getenv("OPENAI_API_KEY")

# Set up LLM
llm = ChatOpenAI(temperature=0, openai_api_key=openai_key)

# Connect to Supabase Postgres
db = SQLDatabase.from_uri(db_uri)

# Create the chain
db_chain = SQLDatabaseChain.from_llm(
    llm=llm,
    db=db,
    verbose=True,
)

# --- Try some queries ---
while True:
    user_question = input("\nAsk a question (or type 'exit'): ")
    if user_question.lower() == "exit":
        break

    try:
        response = db_chain.run(user_question)
        print("\n🔎 Result:\n", response)
    except Exception as e:
        print("⚠️ Error:", e)
