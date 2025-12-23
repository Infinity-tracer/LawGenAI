import streamlit as st
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import re
import requests
import faiss
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# ---------------------- INDIAN KANOON API CONFIG ----------------------
KANOON_API_TOKEN = os.getenv("KANOON_API_TOKEN")
BASE_URL = "https://api.indiankanoon.org"


def strip_html_tags(text):
    """Remove HTML tags from text and decode HTML entities"""
    if not text:
        return ""
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Decode common HTML entities
    clean = clean.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    clean = clean.replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
    return clean.strip()

def _kanoon_headers():
    if not KANOON_API_TOKEN:
        raise ValueError("KANOON_API_TOKEN missing. Please set it in your .env file.")
    return {
        "Authorization": f"Token {KANOON_API_TOKEN}",
        "Accept": "application/json"
    }

def search_cases(query, pagenum=0):
    url = f"{BASE_URL}/search/?formInput={query}&pagenum={pagenum}"
    r = requests.post(url, headers=_kanoon_headers())
    r.raise_for_status()
    return r.json()

def fetch_fragment(doc_id, query):
    url = f"{BASE_URL}/docfragment/{doc_id}/?formInput={query}"
    r = requests.post(url, headers=_kanoon_headers())
    r.raise_for_status()
    return r.json()






def get_pdf_text(pdf_docs):
    text=""
    for pdf in pdf_docs:
        pdf_reader= PdfReader(pdf)
        for page in pdf_reader.pages:
            text+= page.extract_text()
    return  text



def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks


def get_vector_store(text_chunks):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss_index")


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def get_conversational_chain():

    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
    provided context just say, "answer is not available in the context", don't provide the wrong answer

    Context:
    {context}

    Question: {question}

    Answer:
    """
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.3,
        google_api_key=GOOGLE_API_KEY
    )

    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    
    chain = prompt | model | StrOutputParser()

    return chain



def user_input(user_question):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    docs = new_db.similarity_search(user_question)

    chain = get_conversational_chain()

    context = format_docs(docs)
    response = chain.invoke({"context": context, "question": user_question})

    print(response)
    st.write("Reply: ", response)




def kanoon_chat_interface():
    """Indian Kanoon Legal Case Search Interface"""
    st.header("⚖️ Indian Kanoon Legal Chatbot")
    st.caption("Ask legal questions and get relevant case law from Indian Kanoon")

    # Session state for chat history
    if "kanoon_messages" not in st.session_state:
        st.session_state.kanoon_messages = []

    # Display chat history
    for msg in st.session_state.kanoon_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # User input
    query = st.chat_input("Ask a legal question...")

    if query:
        # User message
        st.session_state.kanoon_messages.append({
            "role": "user",
            "content": query
        })
        with st.chat_message("user"):
            st.markdown(query)

        # Assistant response
        with st.chat_message("assistant"):
            with st.spinner("Searching Indian Kanoon..."):
                try:
                    response = search_cases(query)
                    docs = response.get("docs", [])

                    if not docs:
                        reply = "❌ No relevant cases found."
                    else:
                        reply = "### 📄 Relevant Case Law\n\n"

                        for idx, doc in enumerate(docs[:3], start=1):
                            title = strip_html_tags(doc.get("title", "Untitled Case"))

                            # Handle inconsistent Kanoon IDs safely
                            doc_id = (
                                doc.get("docid")
                                or doc.get("tid")
                                or doc.get("id")
                            )

                            if not doc_id:
                                continue

                            # Try to get headline/snippet from search result first
                            snippet = strip_html_tags(doc.get("headline", ""))
                            
                            # If no headline, try fetching fragment
                            if not snippet:
                                try:
                                    fragment = fetch_fragment(doc_id, query)
                                    snippet = strip_html_tags(fragment.get("fragment", "") or fragment.get("content", ""))
                                except:
                                    snippet = ""

                            if not snippet:
                                snippet = "_No relevant excerpt available._"
                            elif len(snippet) > 700:
                                snippet = snippet[:700] + "..."

                            # Build case link
                            case_link = f"https://indiankanoon.org/doc/{doc_id}/"

                            reply += (
                                f"**{idx}. [{title}]({case_link})**\n\n"
                                f"> {snippet}\n\n"
                                "---\n\n"
                            )

                    st.markdown(reply)

                    st.session_state.kanoon_messages.append({
                        "role": "assistant",
                        "content": reply
                    })

                except Exception as e:
                    error_msg = f"⚠️ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.kanoon_messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })


def pdf_chat_interface():
    """PDF Chat Interface with Gemini"""
    st.header("Chat with PDF using Gemini💁")

    user_question = st.text_input("Ask a Question from the PDF Files")

    if user_question:
        user_input(user_question)

    with st.sidebar:
        st.title("Menu:")
        pdf_docs = st.file_uploader("Upload your PDF Files and Click on the Submit & Process Button", accept_multiple_files=True)
        if st.button("Submit & Process"):
            with st.spinner("Processing..."):
                raw_text = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunks(raw_text)
                get_vector_store(text_chunks)
                st.success("Done")


def main():
    st.set_page_config(
        page_title="NyayAssist - Legal AI Assistant",
        page_icon="⚖️",
        layout="centered"
    )

    st.title("🏛️ NyayAssist - Legal AI Assistant")
    
    # Sidebar for mode selection
    with st.sidebar:
        st.title("🔧 Settings")
        mode = st.radio(
            "Select Mode:",
            ["📄 Chat with PDF", "⚖️ Indian Kanoon Search"],
            index=0
        )
        st.markdown("---")
    
    # Render the appropriate interface based on selection
    if mode == "📄 Chat with PDF":
        pdf_chat_interface()
    else:
        kanoon_chat_interface()


if __name__ == "__main__":
    main()