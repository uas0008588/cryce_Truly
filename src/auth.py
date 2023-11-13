from flask import Blueprint, request, jsonify
from src.cosntants.http_status_codes import (
    HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED, HTTP_409_CONFLICT)
from werkzeug.security import check_password_hash, generate_password_hash
import validators
from src.database import User, db
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity
    )


auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

@auth.post("/register")
def register():
    usrname = request.json['usrname']
    email = request.json['email']
    password = request.json['password']

    if len(password) < 6:
        return jsonify(
            {'error': "Password is too short"}
        ), HTTP_400_BAD_REQUEST

    if len(usrname) < 3:
        return jsonify(
            {"error": "Username is too short"}
        ), HTTP_400_BAD_REQUEST

    if not usrname.isalnum() or " " in usrname:
        return jsonify({
            "error": "Username should be alphanumeric, also no spaces"
        }), HTTP_400_BAD_REQUEST

    if not validators.email(email):
        return jsonify({'error': 'Email is not valid'}), HTTP_400_BAD_REQUEST

    if User.query.filter_by(email=email).first() is not None:
        return jsonify({'error': "Email is taken"}), HTTP_409_CONFLICT

    if User.query.filter_by(usrname=usrname).first() is not None:
        return jsonify({'error': "Username is taken"}), HTTP_409_CONFLICT

    pwd_hash = generate_password_hash(password)

    user = User(usrname=usrname, password=pwd_hash, email=email)
    db.session.add(user)
    db.session.commit()

    return  jsonify({
        'message': "User created",
        'user': {
            'username': usrname, "email": email
        }

    }), HTTP_201_CREATED

@auth.post('/login')
def login():
    email = request.json.get('email', '')
    password = request.json.get('password', '')
    print(email, password)
    user = User.query.filter_by(email=email).first()

    if user:
        is_pass_correct = check_password_hash(user.password, password)

        if is_pass_correct:
            refresh = create_refresh_token(identity=user.id)
            access = create_access_token(identity=user.id)

            return jsonify({
                'user': {
                    'refresh': refresh,
                    'access': access,
                    'usrname': user.usrname,
                    'email': user.email
                }
            }), HTTP_200_OK
    return jsonify({'error': 'Wrong Credentials'}), HTTP_401_UNAUTHORIZED


@auth.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    return jsonify({
        'usrname': user.usrname,
        'email': user.email
    }), HTTP_200_OK


@auth.get('/refresh_token')
@jwt_required(refresh=True)
def refresh_users_token():
    identity = get_jwt_identity()
    access = create_access_token(identity=identity)
    
    return jsonify({
        'access': access
    }), HTTP_200_OK
    