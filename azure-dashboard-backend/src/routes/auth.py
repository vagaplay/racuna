from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from src.models.user import User, db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register_user():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    name = data.get("name")

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "User with this email already exists"}), 409

    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password_hash=hashed_password, name=name)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully", "user": new_user.to_dict()}), 201

@auth_bp.route("/login", methods=["POST"])
def login_user():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"message": "Invalid credentials"}), 401

    # Criar sessão para o usuário
    session.clear()  # Limpar sessão anterior
    session['user_id'] = user.id
    session['user_email'] = user.email
    session.permanent = True
    
    # Debug: verificar se a sessão foi criada
    print(f"DEBUG: Sessão criada para usuário {user.id}, session_id: {session.get('_id', 'no_id')}")
    
    return jsonify({
        "message": "Login successful", 
        "user": user.to_dict(),
        "session_debug": {
            "user_id": session.get('user_id'),
            "session_id": session.get('_id', 'no_session_id')
        }
    }), 200

@auth_bp.route("/profile/<int:user_id>", methods=["GET"])
def get_user_profile(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@auth_bp.route("/profile/<int:user_id>", methods=["PUT"])
def update_user_profile(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json

    user.name = data.get("name", user.name)
    user.phone_number = data.get("phone_number", user.phone_number)
    user.email = data.get("email", user.email) # Allow email update, but handle uniqueness

    db.session.commit()
    return jsonify({"message": "Profile updated successfully", "user": user.to_dict()}), 200

# TODO: Implement Microsoft Entra ID authentication flow
@auth_bp.route("/login/microsoft", methods=["POST"])
def login_microsoft():
    # This endpoint would typically initiate the OAuth2 flow with Azure AD
    # For now, it's a placeholder.
    return jsonify({"message": "Microsoft Entra ID login initiated (placeholder)"}), 200



@auth_bp.route("/logout", methods=["POST"])
def logout_user():
    session.clear()
    return jsonify({"message": "Logout successful"}), 200

@auth_bp.route("/me", methods=["GET"])
def get_current_user():
    if 'user_id' not in session:
        return jsonify({"error": "Usuário não autenticado"}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return jsonify({"error": "Usuário não encontrado"}), 401
    
    return jsonify({"user": user.to_dict()}), 200

