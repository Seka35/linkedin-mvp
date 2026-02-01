from database import init_db, get_db, Prospect, Campaign, Action
from sqlalchemy import text

def test_database():
    print("🚀 Démarrage du test base de données...")
    
    # 1. Initialiser la DB
    init_db()
    
    # 2. Obtenir une session
    db = next(get_db())
    
    try:
        # 3. Créer un prospect test
        print("📝 Création d'un prospect test...")
        test_prospect = Prospect(
            linkedin_url="https://www.linkedin.com/in/jdoe-test",
            full_name="John Doe",
            headline="CEO at Test Corp",
            status="new",
            source="test_script"
        )
        db.add(test_prospect)
        db.commit()
        db.refresh(test_prospect)
        print(f"✅ Prospect créé avec ID: {test_prospect.id}")
        
        # 4. Vérifier la lecture
        retrieved = db.query(Prospect).filter_by(linkedin_url="https://www.linkedin.com/in/jdoe-test").first()
        if retrieved and retrieved.full_name == "John Doe":
            print(f"✅ Lecture réussie: {retrieved.full_name}")
        else:
            print("❌ Échec de la lecture")
            
        # 5. Nettoyage
        print("🧹 Nettoyage du prospect test...")
        db.delete(retrieved)
        db.commit()
        print("✅ Nettoyage terminé")
        
    except Exception as e:
        print(f"❌ Erreur durant le test: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_database()
