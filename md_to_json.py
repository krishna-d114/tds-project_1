import os
import json

MD_DIR = "data/course_markdown"
OUTPUT_FILE = "data/course_content.json"

def md_to_json(md_folder, output_file):
    data = []
    for filename in os.listdir(md_folder):
        if filename.endswith(".md"):
            with open(os.path.join(md_folder, filename), "r", encoding="utf-8") as f:
                data.append({"filename": filename, "content": f.read()})
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    md_to_json(MD_DIR, OUTPUT_FILE)
    print(f"✅ Markdown files saved to JSON: {OUTPUT_FILE}")