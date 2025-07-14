from flask import Blueprint, jsonify, request
from src.models.system_setting import SystemSetting, db

system_settings_bp = Blueprint("system_settings", __name__)

@system_settings_bp.route("/settings/<string:setting_name>", methods=["GET"])
def get_setting(setting_name):
    setting = SystemSetting.query.filter_by(setting_name=setting_name).first()
    if setting:
        return jsonify(setting.to_dict()), 200
    return jsonify({"message": "Setting not found"}), 404

@system_settings_bp.route("/settings", methods=["POST"])
def create_or_update_setting():
    data = request.json
    setting_name = data.get("setting_name")
    setting_value = data.get("setting_value")

    if not setting_name or not setting_value:
        return jsonify({"message": "Setting name and value are required"}), 400

    setting = SystemSetting.query.filter_by(setting_name=setting_name).first()
    if setting:
        setting.setting_value = setting_value
        db.session.commit()
        return jsonify({"message": "Setting updated successfully", "setting": setting.to_dict()}), 200
    else:
        new_setting = SystemSetting(setting_name=setting_name, setting_value=setting_value)
        db.session.add(new_setting)
        db.session.commit()
        return jsonify({"message": "Setting created successfully", "setting": new_setting.to_dict()}), 201

@system_settings_bp.route("/settings/<string:setting_name>", methods=["PUT"])
def update_setting(setting_name):
    data = request.json
    setting_value = data.get("setting_value")

    if not setting_value:
        return jsonify({"message": "Setting value is required"}), 400

    setting = SystemSetting.query.filter_by(setting_name=setting_name).first()
    if setting:
        setting.setting_value = setting_value
        db.session.commit()
        return jsonify({"message": "Setting updated successfully", "setting": setting.to_dict()}), 200
    return jsonify({"message": "Setting not found"}), 404


