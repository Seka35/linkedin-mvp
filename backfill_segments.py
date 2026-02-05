from database.db import SessionLocal
from database.models import Prospect, Tag
import re
import json

def backfill_and_rename():
    session = SessionLocal()
    print("🚀 Starting Backfill & Rename...")

    # 1. Rename Tags (Idempotent)
    tag_updates = {
        "Segment A": "Segment A (11-100)",
        "Segment B": "Segment B (101-500)",
        "Segment C": "Segment C (501-2000)",
    }
    
    for old_name, new_name in tag_updates.items():
        tag = session.query(Tag).filter_by(name=old_name).first()
        if tag:
            tag.name = new_name
            print(f"✏️  Renamed tag '{old_name}' to '{new_name}'")
        else:
            exists = session.query(Tag).filter_by(name=new_name).first()
            if not exists:
                new_tag = Tag(name=new_name, color='#6c757d') 
                session.add(new_tag)

    session.commit()
    
    # 2. Backfill Existing Prospects
    print("🔄 Backfilling existing prospects...")
    prospects = session.query(Prospect).all()
    count = 0
    updated_size_count = 0
    
    for p in prospects:
        size_to_parse = p.company_size

        # Fallback: Extract from experiences if company_size is missing
        if not size_to_parse and p.experiences:
            try:
                exps = json.loads(p.experiences)
                if exps and isinstance(exps, list):
                    # Check first experience for companySize
                    first_exp = exps[0]
                    # Format might vary (Apify sometimes nests parsing)
                    if first_exp.get('companySize'):
                        size_to_parse = first_exp.get('companySize')
                    # Sometimes it's in company.companySize? depends on raw structure, 
                    # but ApifyEnricher usually flattens or keeps as is.
                
                if size_to_parse:
                    p.company_size = size_to_parse
                    updated_size_count += 1
            except Exception as e:
                # print(f"Error parsing exp for {p.full_name}: {e}")
                pass

        if not size_to_parse:
            continue
            
        # Robust Parsing
        s_clean = size_to_parse.replace(",", "")
        numbers = re.findall(r'\d+', s_clean)
        
        if not numbers:
            continue
            
        lower = int(numbers[0])
        tag_name = None

        if 1 <= lower <= 10: tag_name = 'Hors Cible'
        elif 11 <= lower <= 100: tag_name = 'Segment A (11-100)'
        elif 101 <= lower <= 500: tag_name = 'Segment B (101-500)'
        elif 501 <= lower <= 2000: tag_name = 'Segment C (501-2000)'
        elif 2001 <= lower <= 5000: tag_name = 'Segment C (501-2000)'
        elif lower > 5000: tag_name = 'Hors Cible'

        if tag_name:
            tag = session.query(Tag).filter_by(name=tag_name).first()
            if tag:
                if tag not in p.tags:
                    p.tags.append(tag)
                    count += 1
                    print(f"   + Tagged {p.full_name} ({size_to_parse}) -> {tag_name}")
    
    session.commit()
    print(f"✅ Backfill complete. Updated size for {updated_size_count} prospects. Enhanced {count} prospects.")
    session.close()

if __name__ == "__main__":
    backfill_and_rename()
