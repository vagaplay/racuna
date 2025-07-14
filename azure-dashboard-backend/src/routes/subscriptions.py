from flask import Blueprint, jsonify, request
from src.models.subscription import Subscription, db
from src.models.user import User

subscriptions_bp = Blueprint("subscriptions", __name__)

@subscriptions_bp.route("/subscriptions", methods=["POST"])
def add_subscription():
    data = request.json
    user_id = data.get("user_id") # Assuming user_id is passed from authenticated session
    subscription_id = data.get("subscription_id")
    subscription_name = data.get("subscription_name")
    tenant_id = data.get("tenant_id")
    auth_type = data.get("auth_type")
    client_id = data.get("client_id")
    client_secret = data.get("client_secret")

    if not all([user_id, subscription_id, subscription_name, tenant_id, auth_type]):
        return jsonify({"message": "Missing required fields"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Basic validation for auth_type
    if auth_type not in ["entra_id", "service_principal"]:
        return jsonify({"message": "Invalid auth_type. Must be 'entra_id' or 'service_principal'"}), 400

    # If auth_type is service_principal, client_id and client_secret are required
    if auth_type == "service_principal" and (not client_id or not client_secret):
        return jsonify({"message": "client_id and client_secret are required for service_principal auth_type"}), 400

    new_subscription = Subscription(
        user_id=user_id,
        subscription_id=subscription_id,
        subscription_name=subscription_name,
        tenant_id=tenant_id,
        auth_type=auth_type,
        client_id=client_id,
        client_secret=client_secret # In a real app, this should be encrypted
    )

    db.session.add(new_subscription)
    db.session.commit()

    return jsonify({"message": "Subscription added successfully", "subscription": new_subscription.to_dict()}), 201

@subscriptions_bp.route("/subscriptions/<int:user_id>", methods=["GET"])
def get_user_subscriptions(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    subscriptions = Subscription.query.filter_by(user_id=user_id).all()
    return jsonify([sub.to_dict() for sub in subscriptions]), 200

@subscriptions_bp.route("/subscriptions/<int:sub_id>", methods=["PUT"])
def update_subscription(sub_id):
    subscription = Subscription.query.get_or_404(sub_id)
    data = request.json

    subscription.subscription_name = data.get("subscription_name", subscription.subscription_name)
    subscription.tenant_id = data.get("tenant_id", subscription.tenant_id)
    subscription.auth_type = data.get("auth_type", subscription.auth_type)
    subscription.client_id = data.get("client_id", subscription.client_id)
    # Only update client_secret if provided, and handle encryption in real app
    if "client_secret" in data:
        subscription.client_secret = data.get("client_secret")

    db.session.commit()
    return jsonify({"message": "Subscription updated successfully", "subscription": subscription.to_dict()}), 200

@subscriptions_bp.route("/subscriptions/<int:sub_id>", methods=["DELETE"])
def delete_subscription(sub_id):
    subscription = Subscription.query.get_or_404(sub_id)
    db.session.delete(subscription)
    db.session.commit()
    return jsonify({"message": "Subscription deleted successfully"}), 204


