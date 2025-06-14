📘 TDS Virtual TA (FastAPI)
A lightweight FastAPI-based Virtual Teaching Assistant designed to help students with the Tools in Data Science (TDS) course. It combines:

Discourse forum Q&A

Course materials

GPT-3.5-turbo via AIPipe API

🔧 Features
📘 Semantic search over Discourse threads

🧠 GPT-generated contextual answers

📎 Returns relevant course and forum links

⚡ Fast and lightweight REST API

📂 Project Structure
bash
Copy
Edit
project-tds-virtual-ta1/
├── data/                      # JSON files: Discourse and course data
│
├── main9.py                  # 🔥 FastAPI app with vector search + GPT answer generation
├── md_to_json.py             # Utility to convert markdown notes to structured JSON
├── scrape_course.py          # Script to scrape official course content
├── scrape_discourse.py       # Script to scrape Discourse posts (from HTML or API)
├── scrape_links.py           # (Likely) helper to link/clean scraped data
│
├── requirements.txt          # All required packages
⚙️ Setup Instructions
1. Clone and Prepare
bash
Copy
Edit
git clone https://github.com/yourusername/tds-virtual-ta.git
cd project-tds-virtual-ta1
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
2. Prepare Data
Make sure data/ contains:

discourse_posts.json

course_content.json

If not, run:

bash
Copy
Edit
python scrape_discourse.py
python scrape_course.py
(Optional) Convert markdown notes:

bash
Copy
Edit
python md_to_json.py
🚀 Running the App
bash
Copy
Edit
uvicorn main9:app --reload
📫 API Usage
Endpoint: POST /api/
Request
json
Copy
Edit
{
  "question": "How do I use bash in the graded assignment?"
}
Response
json
Copy
Edit
{
  "answer": "You can use bash by...",
  "links": [
    {
      "url": "https://example.com/thread1",
      "text": "Use bash in this way..."
    },
    ...
  ]
}
✅ The answer is generated based on top-matching posts and resources.

📌 Code Snippet Highlights
1. Extracting Relevant Forum Posts
python
Copy
Edit
vectorizer = TfidfVectorizer(stop_words="english")
discourse_vectors = vectorizer.fit_transform(discourse_corpus)

similarities = cosine_similarity(vectorizer.transform([question]), discourse_vectors).flatten()
2. Generating GPT Answer
python
Copy
Edit
payload = {
  "model": MODEL_NAME,
  "messages": [{"role": "user", "content": question_with_context}],
  ...
}
response = requests.post(AIPIPE_API_URL, headers=headers, json=payload)
