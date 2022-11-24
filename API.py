import json
import string
from datetime import datetime
import datetime
from bson import ObjectId, json_util
from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient("mongodb://127.0.0.1:27017")
db = client.mydb
media = db.media


@app.route("/api/v1.0/titles", methods=["GET"])
def show_all_titles():
    page_num, page_size = 1, 10
    if request.args.get('pn'):
        page_num = int(request.args.get('pn'))
    if request.args.get('ps'):
        page_size = int(request.args.get('ps'))
    page_start = (page_size * (page_num - 1))

    data_to_return = []
    pipeline = [
        {"$project": {"title": 1}},
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
        return make_response(jsonify({"error": "Invalid business ID"}), 404)

    title = media.find_one({"_id": ObjectId(id)})
    if title is not None:
        for title in media.aggregate(pipeline=[{"$match": {"_id": ObjectId(id)}}, {"$project": {"_id": 0}}, ]):
            return make_response(jsonify(title, 200))
    else:
        return make_response(jsonify({"error": "Invalid business ID"}), 404)


@app.route("/api/v1.0/movies", methods=["GET"])
def show_all_movies():
    page_num, page_size = 1, 10
    if request.args.get('pn'):
        page_num = int(request.args.get('pn'))
    if request.args.get('ps'):
        page_size = int(request.args.get('ps'))
    page_start = (page_size * (page_num - 1))

    data_to_return = []
    pipeline = [
        {"$project": {"title": 1, "_id": 0, "type": 1}},
        {"$match": {"type": "Movie"}},
        {"$skip": page_start},
        {"$limit": page_size}
    ]

    for title in media.aggregate(pipeline):
        data_to_return.append(title)

    return make_response(jsonify(data_to_return), 200)


@app.route("/api/v1.0/series", methods=["GET"])
def show_all_series():
    page_num, page_size = 1, 10
    if request.args.get('pn'):
        page_num = int(request.args.get('pn'))
    if request.args.get('ps'):
        page_size = int(request.args.get('ps'))
    page_start = (page_size * (page_num - 1))

    data_to_return = []
    pipeline = [
        {"$project": {"title": 1, "_id": 0, "type": 1}},
        {"$match": {"type": "TV Show"}},
        {"$skip": page_start},
        {"$limit": page_size}
    ]

    for title in media.aggregate(pipeline):
        data_to_return.append(title)

    return make_response(jsonify(data_to_return), 200)


@app.route("/api/v1.0/titles", methods=["POST"])
def add_title():
    if "title" in request.form and "type" in request.form and "listed_in" in request.form \
            and "description" in request.form:
        now = datetime.datetime.now()
        new_title = {
            "title": request.form["title"],
            "type": request.form["type"],
            "date_added": now.strftime("%d %B, %Y"),
            "listed_in": request.form["listed_in"],
            "description": request.form["description"],
            "reviews": []
        }
        new_title_id = media.insert_one(new_title)
        new_title_link = "http://localhost:5000/api/v1.0/titles/" + str(new_title_id.inserted_id)
        return make_response(jsonify({"url": new_title_link}), 201)

    else:
        return make_response(jsonify({"error": "Missing form data"}), 404)


@app.route("/api/v1.0/titles/<string:id>", methods=["PUT"])
def edit_title(id):
    if "title" in request.form and "type" in request.form and "listed_in" in request.form \
            and "description" in request.form:
        result = media.update_one(
            {"_id": ObjectId(id)},
            {
                "$set": {
                    "title": request.form["title"],
                    "type": request.form["type"],
                    "listed_in": request.form["listed_in"],
                    "description": request.form["description"],
                    "reviews": []
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
    pipeline = [
        {"$match": {"_id": ObjectId(id)}},
        {"$project": {"reviews": 1, "_id": 0}},
        {"$unwind": '$reviews'},
        {"$sort": {"reviews.date": -1}}
    ]

    for title in media.aggregate(pipeline):
        data_to_return.append(title)

    return make_response(json.loads(json_util.dumps(data_to_return)), 200)


@app.route("/api/v1.0/titles/<string:title_id>/reviews/<string:review_id>", methods=["GET"])
def get_one_review(title_id, review_id):
    if len(title_id) != 24 or not all(c in string.hexdigits for c in title_id):
        return make_response(jsonify({"error": "Invalid title ID"}), 404)
    elif len(review_id) != 24 or not all(c in string.hexdigits for c in review_id):
        return make_response(jsonify({"error": "bad review ID"}), 404)
    else:
        title = media.find_one({"reviews._id": ObjectId(review_id)}, {"_id": 0, "reviews.$": 1})

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
