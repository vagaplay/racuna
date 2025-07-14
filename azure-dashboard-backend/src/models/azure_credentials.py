"""
Modelo para armazenar credenciais Azure de forma segura
"""

from datetime import datetime
from cryptography.fernet import Fernet
import os
import base64
from flask_sqlalchemy import SQLAlchemy

# Importar db do módulo user
from src.models.user import db

class AzureCredentials(db.Model):
    __tablename__ = 'azure_credentials'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    tenant_id = db.Column(db.String(255), nullable=False)
    client_id = db.Column(db.String(255), nullable=False)
    client_secret_encrypted = db.Column(db.Text, nullable=False)  # Criptografado
    subscription_id = db.Column(db.String(255), nullable=False)
    subscription_name = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_validated = db.Column(db.DateTime)
    
    # Relacionamento com usuário
    # user = db.relationship('User', backref=db.backref('azure_credentials', uselist=False))
    
    def __init__(self, user_id, tenant_id, client_id, client_secret, subscription_id, subscription_name=None):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret_encrypted = self._encrypt_secret(client_secret)
        self.subscription_id = subscription_id
        self.subscription_name = subscription_name
    
    def _get_encryption_key(self):
        """Obtém chave de criptografia fixa para debug"""
        # Gerar chave válida de 32 bytes para Fernet
        import hashlib
        fixed_string = "BOLT_Dashboard_Encryption_Key_2024"
        key_bytes = hashlib.sha256(fixed_string.encode()).digest()
        return base64.urlsafe_b64encode(key_bytes)
    
    def _encrypt_secret(self, secret):
        """Criptografa o client secret"""
        key = self._get_encryption_key()
        f = Fernet(key)
        return f.encrypt(secret.encode()).decode()
    
    def get_client_secret(self):
        """Descriptografa e retorna o client secret"""
        key = self._get_encryption_key()
        f = Fernet(key)
        return f.decrypt(self.client_secret_encrypted.encode()).decode()
    
    def update_credentials(self, tenant_id=None, client_id=None, client_secret=None, 
                          subscription_id=None, subscription_name=None):
        """Atualiza credenciais"""
        if tenant_id:
            self.tenant_id = tenant_id
        if client_id:
            self.client_id = client_id
        if client_secret:
            self.client_secret_encrypted = self._encrypt_secret(client_secret)
        if subscription_id:
            self.subscription_id = subscription_id
        if subscription_name:
            self.subscription_name = subscription_name
        
        self.updated_at = datetime.utcnow()
    
    def mark_as_validated(self):
        """Marca credenciais como validadas"""
        self.last_validated = datetime.utcnow()
        self.is_active = True
    
    def deactivate(self):
        """Desativa credenciais"""
        self.is_active = False
    
    def to_dict(self, include_secret=False):
        """Converte para dicionário"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'tenant_id': self.tenant_id,
            'client_id': self.client_id,
            'subscription_id': self.subscription_id,
            'subscription_name': self.subscription_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_validated': self.last_validated.isoformat() if self.last_validated else None
        }
        
        if include_secret:
            data['client_secret'] = self.get_client_secret()
        
        return data
    
    @classmethod
    def get_by_user_id(cls, user_id):
        """Obtém credenciais por ID do usuário"""
        return cls.query.filter_by(user_id=user_id, is_active=True).first()
    
    @classmethod
    def delete_by_user_id(cls, user_id):
        """Remove credenciais de um usuário"""
        credentials = cls.query.filter_by(user_id=user_id).first()
        if credentials:
            db.session.delete(credentials)
            db.session.commit()
            return True
        return False

