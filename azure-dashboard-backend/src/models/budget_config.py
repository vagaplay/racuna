from src.models.user import db

class BudgetConfig(db.Model):
    __tablename__ = 'budget_configs'
    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False)
    budget_amount = db.Column(db.DECIMAL(10,2), nullable=False)
    alert_threshold = db.Column(db.DECIMAL(5,2), nullable=False)
    auto_delete = db.Column(db.Boolean, default=False)
    email_confirmation = db.Column(db.Boolean, default=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    subscription = db.relationship('Subscription', backref=db.backref('budget_configs', lazy=True))

    def __repr__(self):
        return f'<BudgetConfig {self.budget_amount} for Sub {self.subscription_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'subscription_id': self.subscription_id,
            'budget_amount': str(self.budget_amount),
            'alert_threshold': str(self.alert_threshold),
            'auto_delete': self.auto_delete,
            'email_confirmation': self.email_confirmation,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat()
        }


