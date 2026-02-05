from database import SessionLocal, Tag

def migrate_signal_names():
    session = SessionLocal()
    print("🔄 Renaming Signal Tags to match specific user requirements...")

    # Mapping Old Name -> New Name
    # We keep the "Signal: " prefix for internal consistency if needed, 
    # but the user sees what we display. 
    # Let's check how we display them. 
    # The UI currently does `tag.name.replace('Signal: ', '')`.
    # So if I name it "Signal: Platform/DevEx initiatives", it displays "Platform/DevEx initiatives".
    
    mapping = {
        "Signal: Platform": "Signal: Platform/DevEx initiatives",
        "Signal: DevEx": "Signal: Platform/DevEx initiatives", # Merge these two? User grouped them.
        "Signal: AI Coding": "Signal: AI coding mentions",
        "Signal: Scaling": "Signal: scaling/hiring",
        "Signal: Productivity": "Signal: productivity investment",
        "Signal: Refactor": "Signal: refactor/tech debt narratives"
    }

    for old, new in mapping.items():
        tag = session.query(Tag).filter_by(name=old).first()
        if tag:
            # Check if target already exists (merge case)
            existing_target = session.query(Tag).filter_by(name=new).first()
            if existing_target:
                print(f"⚠️ Target '{new}' already exists. Merging '{old}' into it...")
                # We would need to reassign prospects, but for simple rename let's just delete old if empty or handle properly.
                # Simpler: just rename if unique.
                # If merging (DevEx + Platform), we need to update prospects.
                for p in tag.prospects:
                    if existing_target not in p.tags:
                        p.tags.append(existing_target)
                session.delete(tag)
            else:
                tag.name = new
                print(f"✅ Renamed '{old}' -> '{new}'")

    session.commit()
    session.close()
    print("✨ Migration Complete.")

if __name__ == "__main__":
    migrate_signal_names()
