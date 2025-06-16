import streamlit as st
import os
import pandas as pd
import csv
import uuid
from langchain.docstore.document import Document
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

#setup before everything else
st.set_page_config(page_title="NYC Orgs AI", layout="wide")


#Password setup
GENERAL_PASSWORD = "pythiatest"
KEYS_FILE = "org_data/access_keys.csv"

# Init state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "org_access_key" not in st.session_state:
    st.session_state.org_access_key = None

def is_valid_key(key):
    if not os.path.isfile(KEYS_FILE):
        return False
    with open(KEYS_FILE, "r", encoding="utf-8") as f:
        return key.strip() in [line.strip() for line in f.readlines()]

#Access Prompt
if not st.session_state.authenticated:
    st.markdown("## 🔐 Private Access Required")
    access_method = st.radio("How would you like to access?", ["Enter general password (use if new to program)", "I have an org access key (use if already submitted org data)"])

    if access_method == "Enter general password (use if new to program)":
        pw = st.text_input("Enter password:", type="password")
        if pw == GENERAL_PASSWORD:
            st.session_state.authenticated = True
            st.success("✅ Access granted!")
            st.experimental_rerun()
        elif pw:
            st.error("❌ Incorrect password.")

    elif access_method == "I have an org access key (use if already submitted org data)":
        entered_key = st.text_input("Enter your access key:")
        if entered_key:
            if is_valid_key(entered_key):
                st.session_state.authenticated = True
                st.session_state.org_access_key = entered_key
                st.success("✅ Access granted via org key!")
                st.experimental_rerun()
            else:
                st.error("❌ Invalid key. Please try again.")

    st.stop()  # Block access until one method passes

#Auth passed — now show the app
st.title("NYC Orgs & Electeds Chatbot")


#Interface setup
st.title("NYC Orgs & Electeds Chatbot")
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

#Session Initialization
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "has_submitted_org" not in st.session_state:
    st.session_state.has_submitted_org = False

#Load Data Function
def load_data():
    docs = []
    data_files = {
        "Orgs": "org_data/issue_database - Orgs.csv",
        "Electeds": "org_data/issue_database - Electeds.csv",
        "Zips": "org_data/issue_database - Zips.csv"
    }
    for tag, file_path in data_files.items():
        df = pd.read_csv(file_path)
        for _, row in df.iterrows():
            content = "\n".join([f"{col}: {row[col]}" for col in df.columns if pd.notna(row[col])])
            docs.append(Document(page_content=content, metadata={"source": tag}))
    embeddings = OpenAIEmbeddings()
    db = FAISS.from_documents(docs, embeddings)
    return db

#Chat Prompt + Chain
prompt = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are an expert assistant trained on NYC organizations working on political and social causes. Use the exact information from the documents below to answer the question. Do not guess or make up organization names or contact information. Be specific and accurate.

Context:
{context}

Question: {question}

Answer:
"""
)

#Process Org Submission
csv_file = "org_data/issue_database - Orgs.csv"
csv_columns = [
    "Influenced Elected",
    "What have we done with them?",
    "Main Issues worked on",
    "Location",
    "Name of Organization",
    "Phone Number",
    "Email",
    "Contact Name",
    "Additional Email",
    "Influence Score"
]

if "org_form_submitted" in st.session_state and st.session_state.org_form_submitted:
    # 🔐 Generate a key and store it
    access_key = str(uuid.uuid4())[:8]  # Short unique key
    st.session_state.authenticated = True  # Grant immediate access
    st.session_state.org_access_key = access_key

    # Save key to file
    with open(KEYS_FILE, "a", encoding="utf-8") as f:
        f.write(access_key + "\n")

    st.success(f"✅ Submission received! Your access key is:\n\n`{access_key}`\n\nSave this for future access.")

    st.session_state.has_submitted_org = True
    st.session_state.chat_history = []

    new_row = st.session_state.org_data
    for col in csv_columns:
        if col not in new_row:
            new_row[col] = ""

    file_exists = os.path.isfile(csv_file)
    with open(csv_file, "a", encoding='utf-8') as f:
        f.write("\n")
    with open(csv_file, "a", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=csv_columns, quoting=csv.QUOTE_ALL)
        if not file_exists:
            writer.writeheader()
        writer.writerow(new_row)

    db = load_data()
    qa = RetrievalQA.from_chain_type(
        llm=OpenAI(),
        retriever=db.as_retriever(),
        chain_type_kwargs={"prompt": prompt}
    )

    st.session_state.org_form_submitted = False

#Load DB + QA on startup or refresh
if "qa" not in st.session_state:
    db = load_data()
    qa = RetrievalQA.from_chain_type(
        llm=OpenAI(),
        retriever=db.as_retriever(),
        chain_type_kwargs={"prompt": prompt}
    )
    st.session_state.qa = qa

#Tabs: Chat & Submit
tab1, tab2 = st.tabs(["💬 Chat", "📤 Submit Your Org"])

#Chat Interface
with tab1:
    if not (st.session_state.has_submitted_org or st.session_state.org_access_key):
        st.info("🛑 To use this chatbot, please submit your organization's info or enter a valid access key.")
    else:
        # ✅ Chatbot UI appears here
        for speaker, msg in st.session_state.chat_history:
            st.markdown(f"**{'🧑 You' if speaker == 'You' else '🤖 Bot'}:** {msg}")

        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_input("Ask a question about NYC orgs or elected officials:", key="input")
            submitted_chat = st.form_submit_button("Send")

        if submitted_chat and user_input:
            with st.spinner("Thinking..."):
                response = st.session_state.qa.run(user_input)
            st.session_state.chat_history.append(("You", user_input))
            st.session_state.chat_history.append(("Bot", response))
            st.experimental_rerun()  # Forces an immediate rerun to display the new chat messages

#Submission Form
with tab2:
    st.header("Submit a New Organization")
    with st.form("org_submission_form"):
        name = st.text_input("📝 Organization Name")
        location = st.text_input("📍 Location (borough or neighborhood)")
        phone = st.text_input("📞 Phone Number")
        email = st.text_input("📧 Email")
        contact_name = st.text_input("👤 Contact Person")
        tags = st.text_input("🏷️ Issue Areas (comma-separated, e.g. Housing, Immigrant Rights)")

        submitted = st.form_submit_button("Submit")

        if submitted:
            st.session_state.org_form_submitted = True
            st.session_state.org_data = {
                "Name of Organization": name,
                "Location": location,
                "Phone Number": phone,
                "Email": email,
                "Contact Name": contact_name,
                "Main Issues worked on": tags
            }
            st.success("✅ Thank you! Your organization has been submitted. Redirecting to chatbot...")
            st.experimental_rerun()