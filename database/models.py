"""
Modèles de base de données SQLAlchemy.
3 tables principales: Prospect, Campaign, Action
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base


class Account(Base):
    """Compte LinkedIn (Multi-comptes)"""
    __tablename__ = 'accounts'

    id = Column(Integer, primary_key=True)
    name = Column(String)  # Nom du compte (ex: "Seka Perso")
    email = Column(String, unique=True, nullable=False)
    
    # Configuration LinkedIn
    li_at_cookie = Column(Text)
    
    # Configuration Proxy
    proxy_url = Column(String)
    proxy_username = Column(String)
    proxy_username = Column(String)
    proxy_password = Column(String)
    proxy_enabled = Column(Boolean, default=True)  # Toggle ON/OFF sans supprimer les infos
    proxy_enabled = Column(Boolean, default=True)  # Toggle ON/OFF sans supprimer les infos
    user_agent = Column(String)  # Custom User-Agent per account
    cookie_status = Column(String, default='valid') # 'valid', 'expired', 'unknown'
    
    # Configuration AI
    system_prompt = Column(Text)  # Prompt système spécifique au compte
    
    # État
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    prospects = relationship("Prospect", back_populates="account")
    campaigns = relationship("Campaign", back_populates="account")


class Prospect(Base):
    """Table des prospects LinkedIn"""
    __tablename__ = 'prospects'
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=True) # Nullable pour la migration
    linkedin_url = Column(String, nullable=False) # Removed unique=True constraint globally, managed by application logic per account if needed, or composite unique index later
    full_name = Column(String)
    headline = Column(String)
    company = Column(String)
    location = Column(String)
    profile_picture = Column(String)
    
    # Données Enrichies (Apify)
    is_enriched = Column(Boolean, default=False)
    summary = Column(Text)          # Bio / About
    email = Column(String)          # Email pro/perso
    phone = Column(String)          # Téléphone
    skills = Column(Text)           # JSON
    experiences = Column(Text)      # JSON
    education = Column(Text)        # JSON
    languages = Column(Text)        # JSON
    
    # Status du prospect
    status = Column(String, default='new')  # new, connected, messaged, replied
    campaign_id = Column(Integer, ForeignKey('campaigns.id'), nullable=True)  # Tag de campagne
    
    # Métadonnées
    source = Column(String)  # google_serp, apify, manual
    added_at = Column(DateTime, default=datetime.utcnow)
    last_action_at = Column(DateTime)
    
    # Relations
    actions = relationship("Action", back_populates="prospect")
    campaign = relationship("Campaign", back_populates="prospects")
    account = relationship("Account", back_populates="prospects")

class Campaign(Base):
    """Table des campagnes de prospection"""
    __tablename__ = 'campaigns'
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=True) # Nullable pour la migration
    name = Column(String, nullable=False)
    search_query = Column(String)  # Google dork ou critères Apify
    
    # Templates de messages
    connection_message = Column(Text)
    first_message = Column(Text)
    message_delay_days = Column(Integer, default=3)  # Délai avant d'envoyer le message (jours)
    
    # Configuration
    daily_limit = Column(Integer, default=10)
    use_ai_customization = Column(Boolean, default=False)
    status = Column(String, default='active')  # active, paused, completed
    
    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    actions = relationship("Action", back_populates="campaign")
    prospects = relationship("Prospect", back_populates="campaign")
    account = relationship("Account", back_populates="campaigns")

class Action(Base):
    """Table des actions LinkedIn effectuées"""
    __tablename__ = 'actions'
    
    id = Column(Integer, primary_key=True)
    prospect_id = Column(Integer, ForeignKey('prospects.id'))
    campaign_id = Column(Integer, ForeignKey('campaigns.id'), nullable=True)
    
    # Type d'action
    action_type = Column(String)  # visit, connect, comment, message
    
    # Détails
    message_sent = Column(Text)
    comment_sent = Column(Text)
    post_url = Column(String)  # Pour les commentaires
    
    # Résultat
    status = Column(String)  # pending, success, failed
    error_message = Column(Text)
    
    # Métadonnées
    executed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    prospect = relationship("Prospect", back_populates="actions")
    campaign = relationship("Campaign", back_populates="actions")
    
class Settings(Base):
    """Configuration globale de l'application"""
    __tablename__ = 'settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(Text)

