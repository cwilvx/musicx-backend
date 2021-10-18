from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE='db.sqlite',
    )

    from . import api
    app.register_blueprint(api.bp, url_prefix='/')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
