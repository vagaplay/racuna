from flask import Blueprint, jsonify, request
from src.models.budget_config import BudgetConfig, db
from src.models.subscription import Subscription

budget_bp = Blueprint("budget", __name__)

@budget_bp.route("/budget", methods=["POST"])
def create_budget_config():
    data = request.json
    subscription_id = data.get("subscription_id")
    budget_amount = data.get("budget_amount")
    alert_threshold = data.get("alert_threshold")
    auto_delete = data.get("auto_delete", False)
    email_confirmation = data.get("email_confirmation", False)
    start_date = data.get("start_date")
    end_date = data.get("end_date")

    if not all([subscription_id, budget_amount, alert_threshold, start_date, end_date]):
        return jsonify({"message": "Missing required fields"}), 400

    subscription = Subscription.query.get(subscription_id)
    if not subscription:
        return jsonify({"message": "Subscription not found"}), 404

    new_budget = BudgetConfig(
        subscription_id=subscription_id,
        budget_amount=budget_amount,
        alert_threshold=alert_threshold,
        auto_delete=auto_delete,
        email_confirmation=email_confirmation,
        start_date=start_date,
        end_date=end_date
    )

    db.session.add(new_budget)
    db.session.commit()

    return jsonify({"message": "Budget configuration created successfully", "budget": new_budget.to_dict()}), 201

@budget_bp.route("/budget/<int:sub_id>", methods=["GET"])
def get_budget_config(sub_id):
    budget = BudgetConfig.query.filter_by(subscription_id=sub_id).first()
    if budget:
        return jsonify(budget.to_dict()), 200
    return jsonify({"message": "Budget configuration not found for this subscription"}), 404

@budget_bp.route("/budget/<int:budget_id>", methods=["PUT"])
def update_budget_config(budget_id):
    budget = BudgetConfig.query.get_or_404(budget_id)
    data = request.json

    budget.budget_amount = data.get("budget_amount", budget.budget_amount)
    budget.alert_threshold = data.get("alert_threshold", budget.alert_threshold)
    budget.auto_delete = data.get("auto_delete", budget.auto_delete)
    budget.email_confirmation = data.get("email_confirmation", budget.email_confirmation)
    budget.start_date = data.get("start_date", budget.start_date)
    budget.end_date = data.get("end_date", budget.end_date)

    db.session.commit()
    return jsonify({"message": "Budget configuration updated successfully", "budget": budget.to_dict()}), 200

@budget_bp.route("/budget/<int:budget_id>", methods=["DELETE"])
def delete_budget_config(budget_id):
    budget = BudgetConfig.query.get_or_404(budget_id)
    db.session.delete(budget)
    db.session.commit()
    return jsonify({"message": "Budget configuration deleted successfully"}), 204


