from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    entra_id = db.Column(db.String(255), unique=True, nullable=True) # Para login com Entra ID
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=True)
    phone_number = db.Column(db.String(50), nullable=True)
    password_hash = db.Column(db.String(255), nullable=True) # Para login local
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())

    # Relação com subscriptions
    subscriptions = db.relationship('Subscription', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'

    def to_dict(self):
        return {
            'id': self.id,
            'entra_id': self.entra_id,
            'email': self.email,
            'name': self.name,
            'phone_number': self.phone_number,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat()
        }

    @classmethod
    def get_by_id(cls, user_id):
        """Buscar usuário por ID"""
        try:
            return cls.query.filter_by(id=user_id).first()
        except Exception as e:
            print(f"Erro ao buscar usuário por ID {user_id}: {e}")
            return None

    @classmethod
    def get_by_email(cls, email):
        """Buscar usuário por email"""
        try:
            return cls.query.filter_by(email=email).first()
        except Exception as e:
            print(f"Erro ao buscar usuário por email {email}: {e}")
            return None


