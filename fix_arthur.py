"""
Correction manuelle DB : Reset Arthur Mensch
"""
from database import SessionLocal, Prospect, Action

db = SessionLocal()

# 1. Récupérer Arthur
arthur = db.query(Prospect).filter(Prospect.full_name.like('%Arthur Mensch%')).first()

if arthur:
    print(f"Correction pour : {arthur.full_name} (Actuel: {arthur.status})")
    
    # 2. Remettre statut à 'new'
    arthur.status = 'new'
    # On peut aussi retirer le campaign_id si on veut qu'il soit "neuf" pour être repris plus tard, 
    # mais si on veut qu'il reste dans la campagne pour plus tard, on laisse. 
    # L'utilisateur a dit "supprime juste lui", dans le sens "le faux positif".
    # Je vais reset le status pour qu'il ne soit plus compté comme "Connecté".
    
    # 3. Supprimer l'action de connexion "success"
    actions = db.query(Action).filter(
        Action.prospect_id == arthur.id, 
        Action.action_type == 'connect'
    ).all()
    
    for action in actions:
        db.delete(action)
        print(f"✅ Action 'connect' supprimée (ID: {action.id})")
    
    db.commit()
    print(f"✅ Statut mis à jour : {arthur.status}")

else:
    print("Arthur Mensch non trouvé")

db.close()
