from fastapi import FastAPI
from pydantic import BaseModel
import json
import re
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI()

AIPIPE_API_URL = "https://aipipe.org/openrouter/v1/chat/completions"
AIPIPE_API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjI0ZjIwMDAwNDRAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.A2KoyIox_ZOIdC99q3bscuAsEzD1ayh8L8xW12TTK3w"
MODEL_NAME = "openai/gpt-3.5-turbo-0125"

with open("data/discourse_posts.json", "r", encoding="utf-8") as f:
    discourse_data = json.load(f)

with open("data/course_content.json", "r", encoding="utf-8") as f:
    course_content = json.load(f)

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

def extract_course_links(question):
    if not any(keyword.lower() in question.lower() for keyword in KEYWORDS):
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

def generate_answer_with_aipipe(question, context):
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
    response = requests.post(AIPIPE_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        return "Unable to generate an answer from AIPipe at the moment."

@app.post("/api/")
async def get_answer(q: Question):
    question = q.question
    q_vector = vectorizer.transform([question])
    similarities = cosine_similarity(q_vector, discourse_vectors).flatten()

    # Top discourse links
    top_n = 7
    top_indices = similarities.argsort()[-top_n:][::-1]
    discourse_links = []
    context_texts = []
    for idx in top_indices:
        link = url_map[idx]
        thread = next(item for item in discourse_data if item["url"] == link)
        text = re.sub(r"\s+", " ", thread["posts"][0]["content"].strip())[:400]
        discourse_links.append({"url": link, "text": text})
        context_texts.append(text)

    # Course content links
    course_links = extract_course_links(question)

    # Combine discourse links (priority first) + course links
    combined_links = discourse_links + course_links

    # Deduplicate by URL
    seen_urls = set()
    final_links = []
    for item in combined_links:
        if item.get("url") and item["url"] not in seen_urls:
            final_links.append(item)
            seen_urls.add(item["url"])

    # Prepare combined context for AIPipe
    combined_context = "\n\n".join(context_texts[:5])

    # Generate answer using AIPipe
    answer = generate_answer_with_aipipe(question, combined_context)

    return {
        "answer": answer,
        "links": final_links
    }
