import sys
import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database import SessionLocal, Prospect, Tag
# from database.models import ProspectTag # Not needed
from services.ai_service import AIService

# Constants
BATCH_SIZE = 3
SIGNAL_TAGS = {
    "Platform/DevEx initiatives": "#6f42c1", # Purple
    "AI coding mentions": "#198754",         # Green
    "scaling/hiring": "#fd7e14",             # Orange
    "productivity investment": "#0dcaf0",    # Cyan
    "refactor/tech debt narratives": "#dc3545" # Red
}

def get_or_create_tag(session, name, color):
    tag = session.query(Tag).filter(Tag.name == name).first()
    if not tag:
        tag = Tag(name=name, color=color)
        session.add(tag)
        session.commit()
    return tag

def get_prospects_batch(session, limit=100):
    # Fetch prospects, prioritizing those without ANY signal tags
    # This is a simple implementation: fetch all, then filter in python (for MVP simplicity)
    # Or better: just fetch latest and let the loop skip them.
    
    # Let's fetch strict list of 100 latest
    prospects = session.query(Prospect).order_by(Prospect.id.desc()).limit(limit).all()
    
    # Filter: Keep only if it doesn't have ANY signal tag
    signal_names = list(SIGNAL_TAGS.keys())
    # Note: DB tag names are "Signal: Platform", etc.
    db_signal_names = ["Signal: " + name for name in signal_names]
    
    candidates = []
    for p in prospects:
        has_signal = any(t.name in db_signal_names for t in p.tags)
        if not has_signal:
            candidates.append(p)
            
    return candidates

def run_signal_enrichment():
    session = SessionLocal()
    ai = AIService()

    # 1. Ensure Tags exist
    print("🔧 Ensuring Signal Tags exist...")
    tag_objects = {}
    for name, color in SIGNAL_TAGS.items():
        tag_objects[name] = get_or_create_tag(session, "Signal: " + name, color)

    # 2. Fetch Prospects
    prospects = get_prospects_batch(session, limit=50) # Limit 50 for test
    print(f"🔍 Found {len(prospects)} prospects to analyze.")

    # 3. Process in Batches
    for i in range(0, len(prospects), BATCH_SIZE):
        batch = prospects[i:i+BATCH_SIZE]
        batch_data = []
        for p in batch:
            batch_data.append({
                'id': p.id,
                'headline': p.headline,
                'summary': p.summary,
                'skills': p.skills  # Add skills for better signal detection
            })
        
        print(f"🤖 Sending batch {i//BATCH_SIZE + 1} ({len(batch)} items) to AI...")
        
        # Call AI
        try:
            results = ai.analyze_batch_signals(batch_data)
            
            # Apply Tags
            count_updates = 0
            for p_id_str, tags_found in results.items():
                if not tags_found:
                    continue
                
                p_id = int(p_id_str)
                prospect = session.query(Prospect).get(p_id)
                if not prospect:
                    continue

                for tag_key in tags_found:
                    # Match tag key (e.g. "Platform") to DB Tag object
                    # Note: AI might return "Platform", DB tag is "Signal: Platform"
                    db_tag = tag_objects.get(tag_key)
                    if db_tag:
                        if db_tag not in prospect.tags:
                            prospect.tags.append(db_tag)
                            count_updates += 1
                            print(f"✅ Tagged Prospect {p_id}: {tag_key}")
            
            session.commit()
            print(f"💾 Batch saved. {count_updates} tags applied.")
            
            # Rate limit safety
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ Batch error: {e}")
            session.rollback()

    session.close()
    print("✨ Signal Enrichment Complete!")

if __name__ == "__main__":
    run_signal_enrichment()
