from flask import Blueprint, jsonify, request
from src.models.scheduled_task import ScheduledTask, db
from src.models.subscription import Subscription

scheduled_tasks_bp = Blueprint("scheduled_tasks", __name__)

@scheduled_tasks_bp.route("/scheduled_tasks", methods=["POST"])
def create_scheduled_task():
    data = request.json
    subscription_id = data.get("subscription_id")
    task_type = data.get("task_type")
    cron_expression = data.get("cron_expression")
    enabled = data.get("enabled", True)
    parameters = data.get("parameters")

    if not all([subscription_id, task_type, cron_expression]):
        return jsonify({"message": "Missing required fields"}), 400

    subscription = Subscription.query.get(subscription_id)
    if not subscription:
        return jsonify({"message": "Subscription not found"}), 404

    new_task = ScheduledTask(
        subscription_id=subscription_id,
        task_type=task_type,
        cron_expression=cron_expression,
        enabled=enabled,
        parameters=parameters
    )

    db.session.add(new_task)
    db.session.commit()

    return jsonify({"message": "Scheduled task created successfully", "task": new_task.to_dict()}), 201

@scheduled_tasks_bp.route("/scheduled_tasks/<int:sub_id>", methods=["GET"])
def get_subscription_scheduled_tasks(sub_id):
    subscription = Subscription.query.get(sub_id)
    if not subscription:
        return jsonify({"message": "Subscription not found"}), 404

    tasks = ScheduledTask.query.filter_by(subscription_id=sub_id).all()
    return jsonify([task.to_dict() for task in tasks]), 200

@scheduled_tasks_bp.route("/scheduled_tasks/<int:task_id>", methods=["PUT"])
def update_scheduled_task(task_id):
    task = ScheduledTask.query.get_or_404(task_id)
    data = request.json

    task.task_type = data.get("task_type", task.task_type)
    task.cron_expression = data.get("cron_expression", task.cron_expression)
    task.enabled = data.get("enabled", task.enabled)
    task.parameters = data.get("parameters", task.parameters)

    db.session.commit()
    return jsonify({"message": "Scheduled task updated successfully", "task": task.to_dict()}), 200

@scheduled_tasks_bp.route("/scheduled_tasks/<int:task_id>", methods=["DELETE"])
def delete_scheduled_task(task_id):
    task = ScheduledTask.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Scheduled task deleted successfully"}), 204


