"""
API endpoints pour contrôler les campagnes
À ajouter à app.py avant la ligne "if __name__ == '__main__':"
"""

@app.route('/api/campaign/run', methods=['POST'])
def api_run_campaign():
    """API: Lancer une campagne manuellement"""
    import subprocess
    import threading
    
    data = request.json
    campaign_id = data.get('campaign_id')
    
    db = SessionLocal()
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    
    if not campaign:
        db.close()
        return jsonify({'success': False, 'error': 'Campagne introuvable'})
    
    if campaign.status != 'active':
        db.close()
        return jsonify({'success': False, 'error': 'La campagne doit être active'})
    
    db.close()
    
    # Lancer run_campaigns.py en arrière-plan
    def run_script():
        subprocess.run(['./venv/bin/python', 'run_campaigns.py'], cwd='/home/seka/Desktop/linkedin-mvp')
    
    thread = threading.Thread(target=run_script)
    thread.start()
    
    return jsonify({'success': True, 'message': 'Campagne lancée en arrière-plan'})

@app.route('/api/campaign/pause', methods=['POST'])
def api_pause_campaign():
    """API: Mettre en pause une campagne"""
    data = request.json
    campaign_id = data.get('campaign_id')
    
    db = SessionLocal()
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    
    if campaign:
        campaign.status = 'paused'
        db.commit()
    
    db.close()
    
    return jsonify({'success': True})

@app.route('/api/campaign/resume', methods=['POST'])
def api_resume_campaign():
    """API: Reprendre une campagne"""
    data = request.json
    campaign_id = data.get('campaign_id')
    
    db = SessionLocal()
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    
    if campaign:
        campaign.status = 'active'
        db.commit()
    
    db.close()
    
    return jsonify({'success': True})
