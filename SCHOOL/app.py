import os, sys, sqlite3
os.chdir(os.path.dirname(os.path.abspath(__file__)))   # so "db/school.db" always resolves
sys.path.insert(0, 'db/')

from flask import Flask, render_template, request, redirect, url_for
from dbhelper import *

upload_folder = "static/img"
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = upload_folder


def ensure_image_column() -> None:
    """Add the `image` column to students if the database doesn't have it yet."""
    conn = sqlite3.connect("db/school.db")
    cols = [row[1] for row in conn.execute("PRAGMA table_info(students)")]
    if "image" not in cols:
        conn.execute("ALTER TABLE students ADD COLUMN image varchar(100)")
        conn.commit()
    conn.close()


ensure_image_column()


@app.route("/")
def index() -> None:
    return redirect(url_for('main'))


@app.route("/main")
def main() -> None:
    students: list = getall('students')
    return render_template('main.html', students=students)


@app.route("/register")
def register() -> None:
    return render_template('register.html')


# Called when SAVE is pressed: saves the picture in static/img
# and records its path in the `image` column of school.db.
@app.route("/save", methods=['POST'])
def save() -> None:
    file: any = request.files.get('webcam')
    idno: str = (request.args.get('idno') or '').strip()
    lastname: str = (request.args.get('lastname') or '').strip()
    firstname: str = (request.args.get('firstname') or '').strip()
    course: str = (request.args.get('course') or '').strip()
    level: str = (request.args.get('level') or '').strip()

    if not (file and idno and lastname and firstname and course and level):
        return "Please fill in all fields and take a picture.", 400
    if not idno.isalnum():
        return "IDNO may only contain letters and numbers.", 400
    if len(getrecord('students', idno=idno)) > 0:
        return "IDNO already exists.", 409

    image: str = upload_folder + "/" + idno + ".png"     # e.g. static/img/9001.png
    ok: bool = addrecord('students', idno=idno, lastname=lastname, firstname=firstname,
                         course=course, level=level, image=image)
    if not ok:
        return "Could not save the student.", 500

    file.save(image)
    return "OK", 200


@app.route("/delete/<idno>")
def delete(idno: str) -> None:
    rec: list = getrecord('students', idno=idno)
    deleterecord('students', idno=idno)
    if rec and rec[0]['image'] and os.path.exists(rec[0]['image']):
        os.remove(rec[0]['image'])
    return redirect(url_for('main'))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
