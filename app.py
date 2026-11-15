import time

import streamlit as st

from config import TOP_K
from firebase_client import FirebaseError, create_account, sign_in, validate_config
from rag import KNOWLEDGE_BASE_PATH, RagError, answer_question, build_index, load_knowledge_base


def forget_user():
    for key in ("user", "messages", "auth_email", "auth_password", "notice", "auth_error", "clear_password", "account_created"):
        st.session_state.pop(key, None)


@st.cache_resource(show_spinner="Embedding the travel guide...")
def get_index(_mtime):
    return build_index(load_knowledge_base())


def show_sources(hits, citations):
    with st.expander("Retrieved guide entries and scores"):
        for hit in hits:
            st.markdown(f"**[{hit['id']}] {hit['title']}** · score {hit['score']:.4f}")
            meta = []
            if hit.get("category"):
                meta.append(f"Category: {hit['category']}")
            if hit.get("tags"):
                meta.append("Tags: " + ", ".join(hit["tags"]))
            if meta:
                st.caption(" · ".join(meta))
            st.write(hit["text"])
            st.caption(f"Source: {hit['source']}")
    if citations["cited_ids"]:
        st.caption("Cited: " + ", ".join(citations["cited_ids"]))
    if citations["unknown_ids"]:
        st.warning("The answer cites entries that were not retrieved: " + ", ".join(citations["unknown_ids"]))


st.title("Lumen Travel Assistant · TP. Hồ Chí Minh")
try:
    validate_config()
except FirebaseError as error:
    st.info(str(error))
    st.stop()

if st.session_state.pop("clear_password", False):
    st.session_state["auth_password"] = ""
if st.session_state.pop("account_created", False):
    st.success("Account created. Sign in with the same app credentials.")
if "auth_error" in st.session_state:
    st.error(st.session_state.pop("auth_error"))
if "notice" in st.session_state:
    st.info(st.session_state.pop("notice"))

try:
    if "user" not in st.session_state:
        with st.form("account_form", clear_on_submit=True):
            email = st.text_input("Email", key="auth_email")
            password = st.text_input("Password", type="password", key="auth_password")
            login = st.form_submit_button("Sign in")
            register = st.form_submit_button("Create account")
        if register:
            create_account(email, password)
            st.session_state["account_created"] = True
            st.session_state["clear_password"] = True
            st.rerun()
        elif login:
            user = sign_in(email, password)
            forget_user()
            st.session_state["user"] = user
            st.rerun()
    else:
        user = st.session_state["user"]
        if time.time() >= user["expires_at"]:
            forget_user()
            st.session_state["notice"] = "Your session has expired. Please sign in again."
            st.rerun()
        st.write(f"Signed in as: {user['email']}")
        if st.button("Sign out"):
            forget_user()
            st.rerun()

        messages = st.session_state.setdefault("messages", [])
        for message in messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                if message["role"] == "assistant":
                    show_sources(message["hits"], message["citations"])

        question = st.chat_input("Ask a question")
        if question is not None:
            question = question.strip()
            if not question:
                st.warning("Type a question first.")
            else:
                with st.chat_message("user"):
                    st.write(question)
                try:
                    indexed_documents, doc_vectors = get_index(KNOWLEDGE_BASE_PATH.stat().st_mtime)
                    with st.chat_message("assistant"):
                        with st.spinner("Searching the guide and writing an answer..."):
                            result = answer_question(question, indexed_documents, doc_vectors, TOP_K)
                        st.write(result["answer"])
                        show_sources(result["hits"], result["citations"])
                except RagError as error:
                    st.error(str(error))
                else:
                    messages.append({"role": "user", "content": question})
                    messages.append({"role": "assistant", "content": result["answer"],
                                     "hits": result["hits"], "citations": result["citations"]})
except FirebaseError as error:
    if error.sign_in_again:
        forget_user()
        st.session_state["notice"] = str(error)
        st.rerun()
    if "user" not in st.session_state:
        st.session_state["clear_password"] = True
        st.session_state["auth_error"] = str(error)
        st.rerun()
    st.error(str(error))
