# Lumen Travel Assistant · Ho Chi Minh City (Sign-in + RAG Chat)

This project is a **Streamlit** web application for **Lumen Travel** that helps signed-in users ask travel questions about **Ho Chi Minh City (TP. Hồ Chí Minh), Vietnam**. It protects the chat page with **Firebase Authentication** and answers questions using a **Retrieval-Augmented Generation (RAG)** pipeline powered by **Ollama** (`embeddinggemma` and `qwen3:4b`) over a local travel guide (`knowledge_base.json`).

---

## 1. Student Information

- **Full Name:** Huỳnh Chí Nhân
- **Student ID:** 25127440
- **Chosen City:** Ho Chi Minh City (TP. Hồ Chí Minh), Vietnam

---

## 2. Selected Models & Tech Stack

- **Web Framework:** Streamlit (`1.66.0`)
- **Authentication:** Firebase Authentication (Email/Password via REST API)
- **Embedding Model:** `embeddinggemma` (via Ollama `/api/embed`)
- **Chat Model:** `qwen3:4b` (via Ollama `/api/chat`)
- **Knowledge Base:** `knowledge_base.json` (`G01`–`G15`, 15 entries about Ho Chi Minh City)

---

## 3. System Description

This assistant is built to answer travel questions about Ho Chi Minh City accurately without making up opening hours, ticket prices, or unverified facts. Only signed-in users can open the chat page. When a user asks a question, the system embeds the question, finds the top 5 most similar entries from `knowledge_base.json` using cosine similarity, and asks `qwen3:4b` to answer strictly from those entries in the same language (Vietnamese or English) while citing entry IDs such as `[G05]`. If the guide does not contain the answer, the assistant replies `Tôi không biết dựa trên cẩm nang du lịch.` or `I don't know based on the travel guide.`

Chat history is kept only in `st.session_state` for the current session and is cleared when signing out. No Firestore or external database is used.

Main files in the project:
- **`app.py`**: Builds the Streamlit UI (sign-in/sign-up screen, chat interface, expandable retrieved-sources panel showing category/tags, and clear error messages), caches the embedded guide via `@st.cache_resource`, and manages session state.
- **`firebase_client.py`**: Sends Firebase Authentication REST API requests (`create_account`, `sign_in`, `validate_config`) and translates Firebase error codes into readable messages.
- **`rag.py`**: Loads `knowledge_base.json`, embeds entries (title, category, tags, and text) and questions, retrieves the top-`k` (`k = 5`) entries by cosine similarity, generates answers, and checks citations.
- **`config.py`**: Loads environment variables from `.env` (`FIREBASE_PROJECT_ID`, `FIREBASE_API_KEY`, `OLLAMA_URL`) and sets `EMBED_MODEL`, `CHAT_MODEL`, and `TOP_K`.
- **`knowledge_base.json`**: Contains 15 individual Ho Chi Minh City entries (`id`, `title`, `text`, `source`, `category`, `tags`).

---

## 4. Installation Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/hchinhan/CT_Lab3.git
   cd CT_Lab3
   ```

2. **Create and activate a virtual environment:**
   - On Windows (PowerShell):
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - On macOS / Linux:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Firebase and Ollama:**
   - On **Firebase Console**, create a project, register a Web app (`</>`), and enable **Authentication > Sign-in method > Email/Password**.
   - On **Google Colab**, run the Lab 5 Ollama + Pinggy server notebook (`embeddinggemma` and `qwen3:4b`) and copy the HTTPS Pinggy URL.

5. **Create `.env` from `.env.example`:**
   - On Windows (PowerShell):
     ```powershell
     Copy-Item .env.example .env
     ```
   - On macOS / Linux:
     ```bash
     cp .env.example .env
     ```
   - Fill in `.env` with your values:
     ```env
     FIREBASE_PROJECT_ID=your-project-id
     FIREBASE_API_KEY=your-web-api-key
     OLLAMA_URL=https://your-pinggy-url
     ```

---

## 5. Running the Application

Ensure the Google Colab Ollama + Pinggy server is running, then start the Streamlit app:

```bash
streamlit run app.py
```

Or run directly from the Windows virtual environment without activating it first:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Once started, open the web app at:
- **App URL:** `http://localhost:8501`

Create an account, sign in, and ask travel questions about Ho Chi Minh City. Restart Streamlit after making changes to `.env`.

---

## 6. Test Results

| # | Question | Type | Expected ID | Retrieved IDs | Correct? | If wrong: failed at |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Gợi ý các địa điểm có tuổi đời lâu đời đáng tham quan ở TP.HCM? | Paraphrase | G03 | G05, G01, G03, G02, G06 | Yes | |
| 2 | Dinh Độc Lập mở cửa mấy giờ và giá vé bao nhiêu? | Answerable | G05 | G05, G07, G02, G10, G06 | Yes | |
| 3 | Gợi ý quán cà phê bình dân hoặc tầm trung ở TP.HCM? | Answerable | G12, G13 | G12, G13, G09, G15, G11 | Yes | |
| 4 | Cuối tuần đi với nhóm bạn thích vận động thể thao thì nên đi đâu? | Paraphrase | G10 | G10, G11, G06, G05, G09 | Yes | |
| 5 | Tuyến Metro số 1 Bến Thành - Suối Tiên hiện giá vé bao nhiêu và chạy từ mấy giờ? | Not in guide | none | G04, G05, G07, G06, G11 | Yes | |
| 6 | Sân bay Tân Sơn Nhất có xe buýt đêm chạy thẳng về Khu Sala không? | Not in guide | none | G11, G06, G05, G07, G04 | Yes | |
| 7 | Thảo Cầm Viên Sài Gòn ở đâu và giá vé vào cổng bao nhiêu? | Answerable | G07 | G07, G05, G02, G08, G01 | Yes | |
| 8 | Muốn đi ăn đêm sau 23h30 ở TP.HCM thì còn chỗ nào mở cửa? | Paraphrase | G14 | G11, G06, G15, G09, G04 | No | retrieval |

Failure step values: `missing data`, `retrieval`, or `generation`.

---

## 7. Known Limitations

- The guide contains 15 individual entries focused on selected places in Ho Chi Minh City, so topics outside the guide (such as metro schedules or airport bus routes) return `"Tôi không biết dựa trên cẩm nang du lịch."` or `"I don't know based on the travel guide."`
- Retrieval always returns `k = 5` entries even when none are relevant, so refusing to guess depends on `qwen3:4b` following the system prompt.
- Each question is answered independently without passing earlier chat turns to the model.
- Opening hours and reference prices are collected for guide use and should be double-checked before actual travel.
- The Ollama backend runs on a temporary Google Colab + Pinggy tunnel, so the URL changes each session and the first question after startup takes longer while embedding the guide once.

---

## 8. AI Tools Used

During the development of this project, AI tools were used as a learning and coding assistant for the following tasks, and all code, configuration, and outputs were reviewed manually:

1. **Application Structure and Implementation**
   - Assisted in structuring `app.py`, `firebase_client.py`, `rag.py`, and `config.py` based on the Lab 3–5 reference materials and assignment requirements.
   - Helped explain Streamlit reruns, `st.session_state`, Firebase Authentication REST calls, and the RAG retrieval/generation flow.

2. **Knowledge Base and Environment Guidance**
   - Assisted in classifying Ho Chi Minh City places into `knowledge_base.json` with `category`, `tags`, opening hours, addresses, and price notes for Assignments 3 and 4.
   - Suggested terminal commands for `.venv` setup, `.env` configuration, and troubleshooting Firebase and Pinggy connections.

3. **Documentation Formatting**
   - Helped organize and format `README.md` clearly for installation, running, testing, and submission.

---

## 9. Demonstration Video

- **Video Link:**

YouTube: https://youtu.be/2krZrjLxmiY

GG Drive: https://drive.google.com/drive/folders/1yIOr_NWmzuy0bNUHWTpEU-MjSwbCTKK9
