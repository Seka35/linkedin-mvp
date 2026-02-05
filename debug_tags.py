from database.db import SessionLocal
from database.models import Prospect
import re

def debug_untagged():
    session = SessionLocal()
    prospects = session.query(Prospect).all()
    
    print(f"Total Prospects: {len(prospects)}")
    
    untagged_count = 0
    for p in prospects:
        if not p.tags:
            untagged_count += 1
            print(f"❌ Untagged: {p.full_name}")
            print(f"   - Company Size (DB): '{p.company_size}'")
            
            # Test Parsing
            if p.company_size:
                s_clean = p.company_size.replace(",", "")
                numbers = re.findall(r'\d+', s_clean)
                print(f"   - Regex extracted: {numbers}")
                if numbers:
                    lower = int(numbers[0])
                    print(f"   - Lower bound: {lower}")
            else:
                print("   - No company_size in DB")
                
            print("-" * 30)

    print(f"Total Untagged: {untagged_count}")
    session.close()

if __name__ == "__main__":
    debug_untagged()
