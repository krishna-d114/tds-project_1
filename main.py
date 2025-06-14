from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import re
import requests
import os
from fastapi.middleware.cors import CORSMiddleware
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI()

# enable CORS for GET, POST, OPTIONS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=True,
)

# load your secrets from env
AIPIPE_API_URL = "https://aipipe.org/openrouter/v1/chat/completions"
AIPIPE_API_KEY = os.getenv("AIPIPE_API_KEY")
MODEL_NAME = "openai/gpt-3.5-turbo-0125"

# load scraped data
with open("data/discourse_posts.json", "r", encoding="utf-8") as f:
    discourse_data = json.load(f)

with open("data/course_content.json", "r", encoding="utf-8") as f:
    course_content = json.load(f)

# build TF-IDF
discourse_corpus = []
url_map = []
for thread in discourse_data:
    for post in thread["posts"]:
        combined = f"{thread['title']} {post['content']}"
        discourse_corpus.append(combined)
        url_map.append(thread["url"])

vectorizer = TfidfVectorizer(stop_words="english")
discourse_vectors = vectorizer.fit_transform(discourse_corpus)

KEYWORDS = ["TDS", "tools", "data", "science", "assignment", "GA", "graded", "project", "excel", "bash", "python"]

def extract_course_links(question: str):
    if not any(k.lower() in question.lower() for k in KEYWORDS):
        return []
    links = []
    for entry in course_content:
        url = entry.get("url")
        text = entry.get("title") or entry.get("content") or ""
        if url:
            links.append({
                "url": url,
                "text": re.sub(r"\s+", " ", text.strip())[:400]
            })
    return links

class Question(BaseModel):
    question: str

def generate_answer_with_aipipe(question: str, context: str) -> str:
    if not AIPIPE_API_KEY:
        raise HTTPException(status_code=500, detail="AIPIPE_API_KEY not set")
    headers = {
        "Authorization": f"Bearer {AIPIPE_API_KEY}",
        "Content-Type": "application/json"
    }
    messages = [
        {"role": "system", "content": "You are a helpful assistant answering questions about the Tools in Data Science (TDS) course using the provided resources."},
        {"role": "user", "content": f"Question: {question}\n\nRelevant Content:\n{context}"}
    ]
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.2
    }
    resp = requests.post(AIPIPE_API_URL, headers=headers, json=payload, timeout=20)
    if resp.status_code == 200:
        return resp.json()["choices"][0]["message"]["content"].strip()
    else:
        return "Unable to generate an answer at the moment."

def answer_logic(question: str):
    # embed question
    q_vec = vectorizer.transform([question])
    sims = cosine_similarity(q_vec, discourse_vectors).flatten()

    # pick top discourse links + context texts
    top_n = 7
    idxs = sims.argsort()[-top_n:][::-1]
    discourse_links, context_texts = [], []
    for i in idxs:
        url = url_map[i]
        thread = next(t for t in discourse_data if t["url"] == url)
        snippet = re.sub(r"\s+", " ", thread["posts"][0]["content"].strip())[:400]
        discourse_links.append({"url": url, "text": snippet})
        context_texts.append(snippet)

    # course content
    course_links = extract_course_links(question)

    # dedupe links
    final_links, seen = [], set()
    for item in discourse_links + course_links:
        if item["url"] not in seen:
            final_links.append(item)
            seen.add(item["url"])

    # generate answer
    ctx = "\n\n".join(context_texts[:5])
    answer = generate_answer_with_aipipe(question, ctx)

    return {"answer": answer, "links": final_links}

# unified root handling
@app.api_route("/", methods=["GET", "POST", "OPTIONS"])
async def root_or_query(q: Question = None):
    if q and q.question:
        return answer_logic(q.question)
    return {"status": "ok", "message": "Virtual TA API is live."}

# preserve the /api/ endpoint
@app.post("/api/")
async def api_query(q: Question):
    return answer_logic(q.question)
