from flask import Flask, jsonify, redirect
import os
from src.auth import auth
from src.bookmarks import bookmarks
from src.database import db, Bookmark
from src.cosntants.http_status_codes import (HTTP_404_NOT_FOUND,
                                             HTTP_500_INTERNAL_SERVER_ERROR)
from flask_jwt_extended import JWTManager
from flasgger import Swagger, swag_from
from src.config.swagger import template, swagger_config


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=os.environ.get("SECRET_KEY"),
            SQLALCHEMY_DATABASE_URI=os.environ.get("SQLAlchemy_DB_URI"),
            JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY"),
            SWAGGER={
                'title': "Bookmarks API",
                "uiversion": "3.0.3"
            }
        )
    else:
        app.config.from_mapping(test_config)

    Swagger(app, config=swagger_config, template=template)
    db.init_app(app)
    JWTManager(app)
    app.register_blueprint(auth)
    app.register_blueprint(bookmarks)

    @app.route("/<short_url>", methods=['GET'])
    @swag_from('./docs/short_url.yaml')
    def redirect_to_url(short_url):
        bookmark = Bookmark.query.filter_by(short_url=short_url).first()

        if bookmark:
            bookmark.visits = bookmark.visits+1
            db.session.commit()

            return redirect(bookmark.url)

    @app.errorhandler(HTTP_404_NOT_FOUND)
    def handle_404(e):
        return jsonify({
            'error': 'Not Found'
        }), HTTP_404_NOT_FOUND
    
    @app.errorhandler(HTTP_500_INTERNAL_SERVER_ERROR)
    def handle_500(e):
        return jsonify({
            'error': 'Something went wron, we are working'
        }), HTTP_500_INTERNAL_SERVER_ERROR
    return app

