from flask_sqlalchemy import SQLAlchemy
from src.models.user import db

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_id = db.Column(db.String(255), nullable=False)
    subscription_name = db.Column(db.String(255), nullable=False)
    tenant_id = db.Column(db.String(255), nullable=False)
    auth_type = db.Column(db.String(50), nullable=False) # 'entra_id' or 'service_principal'
    client_id = db.Column(db.String(255), nullable=True)
    client_secret = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Subscription {self.subscription_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subscription_id': self.subscription_id,
            'subscription_name': self.subscription_name,
            'tenant_id': self.tenant_id,
            'auth_type': self.auth_type,
            'client_id': self.client_id,
            'created_at': self.created_at.isoformat()
        }


