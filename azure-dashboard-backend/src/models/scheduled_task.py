from src.models.user import db

class ScheduledTask(db.Model):
    __tablename__ = 'scheduled_tasks'
    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False)
    task_type = db.Column(db.String(50), nullable=False) # 'remove_locks', 'cleanup_resources', 'shutdown_vms', 'check_budget', etc.
    cron_expression = db.Column(db.String(50), nullable=False)
    enabled = db.Column(db.Boolean, default=True)
    last_execution = db.Column(db.TIMESTAMP, nullable=True)
    next_execution = db.Column(db.TIMESTAMP, nullable=True)
    parameters = db.Column(db.Text, nullable=True) # JSON string with task-specific parameters

    subscription = db.relationship('Subscription', backref=db.backref('scheduled_tasks', lazy=True))

    def __repr__(self):
        return f'<ScheduledTask {self.task_type} for Sub {self.subscription_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'subscription_id': self.subscription_id,
            'task_type': self.task_type,
            'cron_expression': self.cron_expression,
            'enabled': self.enabled,
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'next_execution': self.next_execution.isoformat() if self.next_execution else None,
            'parameters': self.parameters
        }


