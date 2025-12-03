import os
import uuid
from datetime import datetime
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from sqlalchemy import func, or_, and_
from dotenv import load_dotenv
from models import SessionLocal, Car

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))

UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_session():
    return SessionLocal()


@app.route("/ping")
def ping():
    try:
        response = requests.get("https://www.google.com", timeout=3)
        if response.status_code == 200:
            return jsonify({"status": "online"})
    except Exception:
        pass
    return jsonify({"status": "offline"})


# --- Google API helpers ---
def google_custom_search(query: str, max_results: int = 5):
    API_KEY = os.environ.get("GOOGLE_API_KEY")
    CX = os.environ.get("GOOGLE_CX")
    if not API_KEY or not CX:
        return []
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": CX,
        "q": query,
        "hl": "ru",
        "gl": "BY",
        "num": max_results,
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return []
        data = response.json()
        items = data.get("items", []) or []
        return [{"title": i.get("title", ""), "url": i.get("link", "")}
                for i in items if i.get("link")]
    except Exception:
        return []


def google_image_search(query: str, max_results: int = 7):
    API_KEY = os.environ.get("GOOGLE_API_KEY")
    CX = os.environ.get("GOOGLE_CX")
    if not API_KEY or not CX:
        return []
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": CX,
        "q": query,
        "hl": "ru",
        "gl": "BY",
        "num": max_results,
        "searchType": "image",
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return []
        data = response.json()
        items = data.get("items", []) or []
        return [{"title": i.get("title", ""), "url": i.get("link", "")}
                for i in items if i.get("link")]
    except Exception:
        return []


def google_video_search(query: str, max_results: int = 4):
    API_KEY = os.environ.get("GOOGLE_API_KEY")
    CX = os.environ.get("GOOGLE_CX")
    if not API_KEY or not CX:
        return []
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": CX,
        "q": query,
        "hl": "ru",
        "gl": "BY",
        "num": max_results,
        "siteSearch": "youtube.com",
        "siteSearchFilter": "i",
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return []
        data = response.json()
        items = data.get("items", []) or []
        return [{"title": i.get("title", ""), "url": i.get("link", "")}
                for i in items if i.get("link")]
    except Exception:
        return []


# --- Search condition builder (multi-word support) ---
def make_search_condition(query_text: str):
    words = [w for w in query_text.lower().split() if w]
    if not words:
        return None
    per_word = []
    for w in words:
        per_word.append(or_(
            func.lower(Car.brand).contains(w),
            func.lower(Car.model).contains(w),
            func.lower(Car.generation).contains(w),
            func.lower(Car.body).contains(w),
            func.lower(Car.engines).contains(w),
            func.lower(Car.country).contains(w),
            func.lower(Car.years).contains(w),
        ))
    return and_(*per_word)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/catalog")
def catalog():
    session = get_session()
    sort = request.args.get("sort", "date").strip()
    query_text = request.args.get("q", "").strip()
    query = session.query(Car)
    cond = make_search_condition(query_text)
    if cond is not None:
        query = query.filter(cond)
    if sort == "name":
        query = query.order_by(Car.brand.asc(), Car.model.asc())
    elif sort == "price_asc":
        query = query.order_by(Car.avg_price_min.asc())
    elif sort == "price_desc":
        query = query.order_by(Car.avg_price_min.desc())
    else:
        query = query.order_by(Car.created_at.desc())
    items = query.all()
    session.close()
    return render_template("catalog.html", items=items, sort=sort, query=query_text)


@app.route("/search")
def search():
    query_text = request.args.get("q", "").strip()
    results_db, results_links, results_images, results_videos = [], [], [], []
    if query_text:
        session = get_session()
        cond = make_search_condition(query_text)
        if cond is not None:
            results_db = session.query(Car).filter(cond).all()
        session.close()
        results_links = google_custom_search(query_text, max_results=5)
        results_images = google_image_search(query_text, max_results=3)
        results_videos = google_video_search(query_text, max_results=2)
    return render_template(
        "search.html",
        query=query_text,
        results_db=results_db,
        results_links=results_links,
        results_images=results_images,
        results_videos=results_videos,
    )


@app.route("/car/<int:car_id>")
def view_car(car_id):
    session = get_session()
    item = session.get(Car, car_id)
    session.close()
    if not item:
        flash("Автомобиль не найден")
        return redirect(url_for("catalog"))
    return render_template("view_car.html", item=item)


@app.route("/add", methods=["GET", "POST"])
def add_car():
    if request.method == "GET":
        return render_template("add_car.html")
    session = get_session()
    data = {
        k: request.form.get(k, "").strip()
        for k in [
            "brand", "model", "generation", "body", "engines", "drive",
            "car_class", "years", "country", "weak_points"
        ]
    }
    avg_price_min = request.form.get("avg_price_min", "")
    avg_price_max = request.form.get("avg_price_max", "")
    data["avg_price_min"] = int(avg_price_min) if avg_price_min.isdigit() else None
    data["avg_price_max"] = int(avg_price_max) if avg_price_max.isdigit() else None
    photo = request.files.get("photo")
    if photo and allowed_file(photo.filename):
        ext = photo.filename.rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        photo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        data["photo_filename"] = filename
    item = Car(**data)
    session.add(item)
    session.commit()
    session.close()
    flash("Автомобиль добавлен")
    return redirect(url_for("catalog"))


@app.route("/edit/<int:car_id>", methods=["GET", "POST"])
def edit_car(car_id):
    session = get_session()
    item = session.get(Car, car_id)
    if not item:
        session.close()
        flash("Автомобиль не найден")
        return redirect(url_for("catalog"))
    if request.method == "GET":
        session.close()
        return render_template("edit_car.html", item=item)
    for field in [
        "brand", "model", "generation", "body", "engines", "drive",
        "car_class", "years", "country", "weak_points"
    ]:
        setattr(item, field, request.form.get(field, "").strip())
    avg_price_min = request.form.get("avg_price_min", "")
    avg_price_max = request.form.get("avg_price_max", "")
    item.avg_price_min = int(avg_price_min) if avg_price_min.isdigit() else None
    item.avg_price_max = int(avg_price_max) if avg_price_max.isdigit() else None

    photo = request.files.get("photo")
    if photo and allowed_file(photo.filename):
        ext = photo.filename.rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        photo.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        item.photo_filename = filename

    item.updated_at = datetime.utcnow()
    session.commit()
    session.close()
    flash("Изменения сохранены")
    return redirect(url_for("view_car", car_id=car_id))


@app.route("/delete/<int:car_id>", methods=["POST"])
def delete_car(car_id):
    session = get_session()
    item = session.get(Car, car_id)
    if item:
        session.delete(item)
        session.commit()
        flash("Автомобиль удалён")
    else:
        flash("Автомобиль не найден")
    session.close()
    return redirect(url_for("catalog"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
