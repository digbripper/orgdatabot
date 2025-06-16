from sqlalchemy import create_engine, text
import pandas as pd

# Replace with your credentials
user = "charliemarshall"
password = "Pur3leaf"
host = "localhost"
port = "5432"
database = "nyc_orgs_db"

# Connect to PostgreSQL
engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}")

# Step 1: Create the table (if not exists)
create_table_sql = """
CREATE TABLE IF NOT EXISTS orgs (
    id SERIAL PRIMARY KEY,
    influenced_elected TEXT,
    projects_worked_on TEXT,
    issues_worked_on TEXT,
    location TEXT,
    name_of_org TEXT,
    phone TEXT,
    email TEXT,
    contact_name TEXT,
    additional_email TEXT,
    influence_score TEXT
);
"""

with engine.connect() as conn:
    conn.execute(text(create_table_sql))
    print("✅ Table ensured.")

    # Step 2: Check what tables exist
    result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
    print("Tables in DB:", [row[0] for row in result])

# Step 3: Load CSV into DataFrame
df = pd.read_csv("org_data/issue_database - Orgs.csv")

# Optional: Rename columns to match database schema (if needed)
df = df.rename(columns={
    "influenced_elected": "influenced_elected",
    "projects_worked_on": "projects_worked_on",
    "issues_worked_on": "issues_worked_on",
    "location": "location",
    "name_of_org": "name_of_org",
    "phone": "phone",
    "email": "email",
    "contact_name": "contact_name",
    "additional_email": "additional_email",
    "influence_score": "influence_score"
})

# Step 4: Upload to PostgreSQL
df.to_sql("orgs", engine, if_exists="append", index=False)
print("✅ Data uploaded to PostgreSQL!")
