
import json
import os

FILE = "sources.json"

def load_sources():
    if not os.path.exists(FILE):
        return []
    with open(FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_sources(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_source():
    data = load_sources()
    name = input("Source name: ").strip()
    url = input("Source URL: ").strip()

    data.append({
        "id": len(data) + 1,
        "name": name,
        "url": url
    })

    save_sources(data)
    print("Source saved!")

def show_sources():
    data = load_sources()

    if not data:
        print("No sources.")
        return

    for x in data:
        print(f"{x['id']}. {x['name']} - {x['url']}")

if __name__ == "__main__":
    print("1. Add Source")
    print("2. View Sources")

    c = input("Choose: ")

    if c == "1":
        add_source()
    elif c == "2":
        show_sources()
