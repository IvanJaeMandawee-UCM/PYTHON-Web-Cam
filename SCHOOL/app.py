import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))   # so "db/school.db" always resolves
sys.path.insert(0, 'db/')

from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from dbhelper import *

upload_folder = "static/img"
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = upload_folder


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


@app.route("/save", methods=['POST', 'GET'])
def save() -> None:
    file: any = request.files.get('webcam')
    idno: str = (request.args.get('idno') or '').strip()
    lastname: str = (request.args.get('lastname') or '').strip()
    firstname: str = (request.args.get('firstname') or '').strip()
    course: str = (request.args.get('course') or '').strip()
    level: str = (request.args.get('level') or '').strip()

    # server-side check (the browser also checks before SNAP)
    if not (file and idno and lastname and firstname and course and level):
        return "Please fill in all fields and take a picture.", 400

    filename: str = upload_folder + "/" + secure_filename(idno) + ".jpg"
    ok: bool = addrecord('students', idno=idno, lastname=lastname,
                         firstname=firstname, course=course, level=level)
    if not ok:
        return "IDNO already exists or could not be saved.", 409

    file.save(filename)
    return "OK", 200


@app.route("/delete/<idno>")
def delete(idno: str) -> None:
    deleterecord('students', idno=idno)
    path: str = upload_folder + "/" + secure_filename(idno) + ".jpg"
    if os.path.exists(path):
        os.remove(path)
    return redirect(url_for('main'))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
