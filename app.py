# ДЗ 17 Шумихин А.В. 21.12.2022
# app.py

from flask import Flask, request
from flask_restx import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
db = SQLAlchemy(app)


class Movie(db.Model):
    __tablename__ = 'movie'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.String(255))
    trailer = db.Column(db.String(255))
    year = db.Column(db.Integer)
    rating = db.Column(db.Float)
    genre_id = db.Column(db.Integer, db.ForeignKey("genre.id"))
    genre = db.relationship("Genre")
    director_id = db.Column(db.Integer, db.ForeignKey("director.id"))
    director = db.relationship("Director")


class Director(db.Model):
    __tablename__ = 'director'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


# TODO: my code ========================================================================================================
api = Api(app)


class MovieSchema(Schema):  # схема сериализации 'фильм'
    id = fields.Int()
    title = fields.Str()
    description = fields.Str()
    trailer = fields.Str()
    year = fields.Int()
    rating = fields.Float()
    genre_id = fields.Int()
    director_id = fields.Int()


class DirectorSchema(Schema):  # схема сериализации 'режиссёр'
    id = fields.Int()
    name = fields.Str()


class GenreSchema(Schema):  # схема сериализации 'жанр'
    id = fields.Int()
    name = fields.Str()


# Инициализация схем
movie_schema = MovieSchema()
movies_schema = MovieSchema(many=True)
director_schema = DirectorSchema()
directors_schema = DirectorSchema(many=True)
genre_schema = GenreSchema()
genres_schema = GenreSchema(many=True)


# Namespases:
movie_ns = api.namespace('movies')
director_ns = api.namespace('directors')
genre_ns = api.namespace('genres')


# VIEWS ================================================================================================================
@movie_ns.route('/<int:mid>')
class MovieView(Resource):
    def get(self, mid):
        movie = Movie.query.get(mid)
        if movie is None:
            return f'Movie with id={mid} not found', 404
        return movie_schema.dump(movie), 200

    def put(self, mid):       
        movie = Movie.query.get(mid)
        if movie is None:
            return f'Movie with id={mid} not found', 404
        
        req_json = request.json
        
        movie.title = req_json.get('title')
        movie.description = req_json.get('description')
        movie.trailer = req_json.get('trailer')
        movie.year = req_json.get('year')
        movie.rating = req_json.get('rating')
        movie.genre_id = req_json.get('genre_id')
        movie.director_id = req_json.get('director_id')
        
        db.session.add(movie)
        db.session.commit()

        return '', 204

    def delete(self, mid):
        movie = db.session.query(Movie).get(mid)
        if not movie:
            return f'Movie with id={mid} not found', 404

        db.session.delete(movie)
        db.session.commit()

        return f'Movie with id={mid} deleted'


@movie_ns.route('/')
class MoviesView(Resource):
    def get(self):
        movies_query = db.session.query(Movie)          # запрос ВСЕХ фильмов из БД

        director_id = request.args.get('director_id')   # аргумент 'режиссёр' из запроса
        if director_id is not None:                     # фильтрация, если есть аргумент
            movies_query = movies_query.filter(Movie.director_id == director_id)

        genre_id = request.args.get('genre_id')         # аргумент 'жанр' из запроса
        if genre_id is not None:                        # фильтрация, если есть аргумент
            movies_query = movies_query.filter(Movie.genre_id == genre_id)

        return movies_schema.dump(movies_query.all()), 200  # сериализация и вывод данных

    def post(self):
        request_json = request.json         # считывание и преобразование параметров из запроса
        new_movie = Movie(**request_json)   # передача параметров в модель СУБД 'Фильм'
        # Добавление кина
        with db.session.begin():
            db.session.add(new_movie)       # добавление фильма в БД

        return f'Movie {new_movie.id} is added', 201


@director_ns.route('/')
class DirectorsView(Resource):
    def get(self):
        all_directors = Director.query.all()                # запрос ВСЕХ режиссёров из БД
        return directors_schema.dump(all_directors), 200    # сериализация и вывод данных


@director_ns.route('/<int:did>')
class DirectorView(Resource):
    def get(self, did):
        director = Director.query.get(did)                  # запрос из БД
        if not director:
            return f'Director with id={did} not found', 404
        return director_schema.dump(director), 200          # сериализация и вывод данных


@genre_ns.route('/')
class GenresView(Resource):
    def get(self):
        all_genres = Genre.query.all()                # запрос ВСЕХ жанров из БД
        return genres_schema.dump(all_genres), 200    # сериализация и вывод данных


@genre_ns.route('/<int:gid>')
class GenreView(Resource):
    def get(self, gid):
        genre = Genre.query.get(gid)                  # запрос из БД
        if not genre:
            return f'Genre with id={gid} not found', 404
        movies_query = Movie.query.filter(Movie.genre_id == gid)
        gen_ret = list()
        gen_ret.append(genre_schema.dump(genre))
        gen_ret.append(movies_schema.dump(movies_query.all()))
        return gen_ret, 200  # сериализация и вывод данных


if __name__ == '__main__':
    app.run(debug=True)
