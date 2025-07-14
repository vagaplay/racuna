from src.models.user import db

class SystemSetting(db.Model):
    __tablename__ = 'system_settings'
    id = db.Column(db.Integer, primary_key=True)
    setting_name = db.Column(db.String(255), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<SystemSetting {self.setting_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'setting_name': self.setting_name,
            'setting_value': self.setting_value
        }


