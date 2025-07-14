from src.models.user import db

class Deployment(db.Model):
    __tablename__ = 'deployments'
    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    deployment_date = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    resources_created = db.Column(db.Text, nullable=True) # JSON string of resources

    subscription = db.relationship('Subscription', backref=db.backref('deployments', lazy=True))

    def __repr__(self):
        return f'<Deployment {self.id} for Sub {self.subscription_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'subscription_id': self.subscription_id,
            'status': self.status,
            'deployment_date': self.deployment_date.isoformat(),
            'resources_created': self.resources_created
        }


