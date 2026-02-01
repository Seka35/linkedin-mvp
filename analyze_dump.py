
import re

filename = "debug_profile_dump.html"

def search_context(keyword, context=500):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
            
        print(f"--- Searching for '{keyword}' ---")
        matches = [m.start() for m in re.finditer(re.escape(keyword), content)]
        
        if not matches:
            print("Not found.")
            return

        print(f"Found {len(matches)} matches.")
        for i, start in enumerate(matches[:3]): # Show first 3
            s = max(0, start - context)
            e = min(len(content), start + len(keyword) + context)
            snippet = content[s:e]
            print(f"Match {i+1}:\n...{snippet}...\n")
            
    except Exception as e:
        print(f"Error: {e}")

search_context("Send")
search_context("Envoyer")
search_context("Add a note")
search_context("Ajouter une note")
search_context("Pending")
search_context("En attente")
search_context("modal")
