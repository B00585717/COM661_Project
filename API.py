import bcrypt
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import string
import jwt
import datetime
from functools import wraps

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'mysecret'

client = MongoClient("mongodb://127.0.0.1:27017")
db = client.mydb
media = db.finalnotflix


@app.route("/api/v1.0/titles", methods=["GET"])
def show_all_titles():
    page_size, page_start = pagination()

    data_to_return = []
    pipeline = [
        {"$project": {
            "title": 1,
            "type": 1,
            "listed_in": 1,
            "cast": 1,
            "description": 1,
            "director": 1,
            "rating": 1,
            "duration": 1,
            "release_year": 1,
            "image": 1,
            "count": {"$size": "$reviews"}
        }
        },
        {"$skip": page_start},
        {"$limit": page_size}
    ]

    for title in media.aggregate(pipeline):
        title['_id'] = str(title['_id'])
        data_to_return.append(title)

    return make_response(jsonify(data_to_return), 200)


@app.route("/api/v1.0/titles/<string:id>", methods=["GET"])
def show_one_title(id):
    if len(id) != 24 or not all(c in string.hexdigits for c in id):
        return make_response(jsonify({"error": "Invalid title ID"}), 404)

    title = media.aggregate([{"$match": {"_id": ObjectId(id)}}])

    if title is not None:
        for title in media.aggregate(
                pipeline=[{"$match": {"_id": ObjectId(id)}},
                          {"$project": {
                              "_id":1,
                              "title": 1,
                              "reviews": 1,
                              "type": 1,
                              "listed_in": 1,
                              "cast": 1,
                              "description": 1,
                              "director": 1,
                              "rating": 1,
                              "duration": 1,
                              "release_year": 1,
                              "image": 1,
                              "count": {"$size": "$reviews"}}
                          }
                          ]):
            title['_id'] = str(title['_id'])
            for review in title["reviews"]:
                review["_id"] = str(review["_id"])
            return make_response(jsonify([title]), 200)
    else:
        return make_response(jsonify({"error": "Invalid title ID"}), 404)


@app.route("/api/v1.0/movies", methods=["GET"])
def show_all_movies():
    page_size, page_start = pagination()

    data_to_return = []
    pipeline = [
        {"$project": {
            "title": 1,
            "type": 1,
            "listed_in": 1,
            "description": 1,
            "image": 1,
            "count": {"$size": "$reviews"}
        }
        },
        {"$match": {"type": "Movie"}},
        {"$skip": page_start},
        {"$limit": page_size}
    ]

    for title in media.aggregate(pipeline):
        title['_id'] = str(title['_id'])
        data_to_return.append(title)

    return make_response(jsonify(data_to_return), 200)


@app.route("/api/v1.0/titles/genre/<string:genre>", methods=["GET"])
def show_genre(genre):
    data_to_return = []
    pipeline = [
        {"$project": {
            "title": 1,
            "type": 1,
            "listed_in": 1,
            "description": 1,
            "image": 1,
            "count": {"$size": "$reviews"}}
        },
        {"$match": {"listed_in": genre}
         }]

    for title in media.aggregate(pipeline):
        title['_id'] = str(title['_id'])
        data_to_return.append(title)

    return make_response(jsonify(data_to_return), 200)


@app.route("/api/v1.0/series", methods=["GET"])
def show_all_series():
    page_size, page_start = pagination()

    data_to_return = []
    pipeline = [
        {"$project": {
            "title": 1,
            "type": 1,
            "listed_in": 1,
            "description": 1,
            "image": 1,
            "count": {"$size": "$reviews"}
        }
        },
        {"$match": {"type": "TV Show"}},
        {"$skip": page_start},
        {"$limit": page_size}
    ]

    for title in media.aggregate(pipeline):
        title['_id'] = str(title['_id'])
        data_to_return.append(title)

    return make_response(jsonify(data_to_return), 200)


def pagination():
    page_num, page_size = 1, 5
    if request.args.get('pn'):
        page_num = int(request.args.get('pn'))
    if request.args.get('ps'):
        page_size = int(request.args.get('ps'))
    page_start = (page_size * (page_num - 1))
    return page_size, page_start


@app.route("/api/v1.0/titles", methods=["POST"])
def add_title():
    if "title" in request.form \
            and "type" in request.form \
            and "listed_in" in request.form \
            and "description" in request.form \
            and "rating" in request.form \
            and "director" in request.form \
            and "duration" in request.form \
            and "cast" in request.form \
            and "release_year" in request.form \
            and "image" in request.form:
        now = datetime.datetime.now()
        new_title = {
            "title": request.form["title"],
            "type": request.form["type"],
            "date_added": now.strftime("%d %B, %Y"),
            "listed_in": request.form["listed_in"],
            "description": request.form["description"],
            "reviews": [],
            "rating": request.form["rating"],
            "director": request.form["director"],
            "duration": request.form["duration"],
            "cast": request.form["cast"],
            "release_year": request.form["release_year"],
            "image": request.form["image"]
        }
        new_title_id = media.insert_one(new_title)
        new_title_link = "http://localhost:5000/api/v1.0/titles/" + str(new_title_id.inserted_id)
        return make_response(jsonify({"url": new_title_link}), 201)

    else:
        return make_response(jsonify({"error": "Missing form data"}), 404)


@app.route("/api/v1.0/titles/<string:id>", methods=["PUT"])
def edit_title(id):
    if "title" in request.form \
            and "type" in request.form \
            and "listed_in" in request.form \
            and "description" in request.form \
            and "rating" in request.form \
            and "director" in request.form \
            and "duration" in request.form \
            and "cast" in request.form \
            and "release_year" in request.form \
            and "image" in request.form:
        result = media.update_one(
            {"_id": ObjectId(id)},
            {
                "$set": {
                    "title": request.form["title"],
                    "type": request.form["type"],
                    "listed_in": request.form["listed_in"],
                    "description": request.form["description"],
                    "rating": request.form["rating"],
                    "director": request.form["director"],
                    "duration": request.form["duration"],
                    "cast": request.form["cast"],
                    "release_year": request.form["release_year"],
                    "image": request.form["image"]
                }
            }
        )
        if result.matched_count == 1:
            edit_title_link = "http://localhost:5000/api/v1.0/titles/" + id
            return make_response(jsonify({"url": edit_title_link}), 200)
        else:
            return make_response(jsonify({"error": "Invalid title ID"}), 404)
    else:
        return make_response(jsonify({"error": "Missing form data"}), 404)


@app.route("/api/v1.0/titles/<string:id>", methods=["DELETE"])
def delete_title(id):
    result = media.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 1:
        return make_response(jsonify({}), 204)
    else:
        return make_response(jsonify({"error": "Invalid title ID"}), 404)


@app.route("/api/v1.0/titles/<string:id>/reviews", methods=["GET"])
def show_all_reviews(id):
    if len(id) != 24 or not all(c in string.hexdigits for c in id):
        return make_response(jsonify({"error": "Invalid title ID"}), 404)

    data_to_return = []
    title = media.find_one(
        {"_id": ObjectId(id)}, {"reviews": 1, "_id": 1}
    )

    for review in title["reviews"]:
        review["_id"] = str(review["_id"])
        data_to_return.append(review)

    sorted_data_by_date = sorted(data_to_return, key=lambda k: k['date'], reverse=True)

    return make_response(jsonify(sorted_data_by_date), 200)


@app.route("/api/v1.0/titles/<string:title_id>/reviews/<string:review_id>", methods=["GET"])
def get_one_review(title_id, review_id):
    if len(title_id) != 24 or not all(c in string.hexdigits for c in title_id):
        return make_response(jsonify({"error": "Invalid title ID"}), 404)
    elif len(review_id) != 24 or not all(c in string.hexdigits for c in review_id):
        return make_response(jsonify({"error": "bad review ID"}), 404)
    else:
        title = media.find_one({"reviews._id": ObjectId(review_id)}, {"_id": 1, "reviews.$": 1})

        if title is not None:
            title['reviews'][0]['_id'] = str(title['reviews'][0]['_id'])
            return make_response(jsonify(title['reviews'][0]), 200)
        else:
            return make_response(jsonify({"error": "Invalid title ID or review ID"}), 404)


@app.route("/api/v1.0/titles/<string:id>/reviews", methods=["POST"])
def add_new_review(id):
    now = datetime.datetime.now()
    new_review = {
        "_id": ObjectId(),
        "date": now.strftime("%Y-%m-%d, %H:%M:%S"),
        "name": request.form["name"],
        "text": request.form["text"],
        "stars": request.form["stars"]
    }
    media.update_one(
        {"_id": ObjectId(id)},
        {
            "$push": {"reviews": new_review}
        }
    )
    new_review_link = "http://localhost:5000/api/v1.0/titles/" + id + "/reviews/" + str(new_review["_id"])
    return make_response(jsonify({"url": new_review_link}), 201)


@app.route("/api/v1.0/titles/<string:title_id>/reviews/<string:review_id>", methods=["PUT"])
def edit_review(title_id, review_id):
    if len(title_id) != 24 or not all(c in string.hexdigits for c in title_id):
        return make_response(jsonify({"error": "Invalid title ID"}), 404)
    elif len(review_id) != 24 or not all(c in string.hexdigits for c in review_id):
        return make_response(jsonify({"error": "bad review ID"}), 404)
    else:
        edited_review = {
            "reviews.$.name": request.form["name"],
            "reviews.$.text": request.form["text"],
            "reviews.$.stars": request.form["stars"]
        }
        if "name" in request.form and "text" in request.form and "stars" in request.form:
            media.update_one(
                {"reviews._id": ObjectId(review_id)},
                {"$set": edited_review}
            )
            edit_review_url = "http://localhost:5000/api/v1.0/titles/" + title_id + "/reviews/" + review_id
            return make_response(jsonify({"url": edit_review_url}, 200))


@app.route("/api/v1.0/titles/<string:title_id>/reviews/<string:review_id>", methods=["DELETE"])
def delete_review(title_id, review_id):
    if len(title_id) != 24 or not all(c in string.hexdigits for c in title_id):
        return make_response(jsonify({"error": "Invalid title ID"}), 404)
    elif len(review_id) != 24 or not all(c in string.hexdigits for c in review_id):
        return make_response(jsonify({"error": "bad review ID"}), 404)
    else:
        media.update_one(
            {"_id": ObjectId(title_id)},
            {"$pull": {"reviews": {"_id": ObjectId(review_id)}}}
        )
        return make_response(jsonify({}), 204)


if __name__ == "__main__":
    app.run(debug=True)
