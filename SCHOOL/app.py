import os, sys, sqlite3, socket
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 'db/')

from flask import Flask, render_template, request, redirect, url_for
from dbhelper import *
from werkzeug.serving import BaseWSGIServer

upload_folder = "static/img"
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = upload_folder


def ensure_image_column() -> None:
    conn = sqlite3.connect("db/school.db")
    cols = [row[1] for row in conn.execute("PRAGMA table_info(students)")]
    if "image" not in cols:
        conn.execute("ALTER TABLE students ADD COLUMN image varchar(100)")
        conn.commit()
    conn.close()


ensure_image_column()


COURSES = {"bsit": "Information Technology", "bscs": "Computer Science", "dait": "Applied IT"}
LEVELS = {"1": "First Year", "2": "Second Year", "3": "Third Year", "4": "Fourth Year"}


ALLOW_PHONES = False

ALLOWED_PREFIX = "172.17.16."

SERVER_ADDRESS = ""


def all_ips() -> list:
    found: list = []

    def add(ip: str) -> None:
        if ip and not ip.startswith(("127.", "169.254.", "0.")) and ip not in found:
            found.append(ip)

    targets = ["172.17.16.1", "8.8.8.8", "192.168.1.1", "192.168.0.1", "10.0.0.1", "172.16.0.1"]
    for target in targets:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect((target, 80))
            add(sock.getsockname()[0])
        except Exception:
            pass
        finally:
            sock.close()
    try:
        for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
            add(ip)
    except Exception:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            add(info[4][0])
    except Exception:
        pass
    if os.name == "nt":
        try:
            import re, subprocess
            out = subprocess.run(["ipconfig"], capture_output=True, text=True, timeout=5).stdout
            for ip in re.findall(r"IPv4[^:\n]*:\s*(\d+\.\d+\.\d+\.\d+)", out):
                add(ip)
        except Exception:
            pass
    return found


def lan_ips() -> list:
    ips = all_ips()
    if ALLOWED_PREFIX:
        ips = [ip for ip in ips if ip.startswith(ALLOWED_PREFIX)]
    return ips


def base_url() -> str:
    name, _, port = request.host.partition(":")
    if not ALLOW_PHONES:
        name = "127.0.0.1"
    elif SERVER_ADDRESS:
        name = SERVER_ADDRESS
    elif not (ALLOWED_PREFIX and name.startswith(ALLOWED_PREFIX)):
        ips = lan_ips()
        if ips:
            name = ips[0]
        elif ALLOWED_PREFIX or name == "localhost":
            name = "127.0.0.1"
    return f"{request.scheme}://{name}:{port or 80}/"


@app.route("/")
def index() -> None:
    return redirect(url_for('main'))


@app.route("/main")
def main() -> None:
    students: list = getall('students')
    return render_template('main.html', students=students, base_url=base_url(),
                           allow_phones=ALLOW_PHONES)


@app.route("/register")
def register() -> None:
    return render_template('register.html', base_url=base_url())


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

    image: str = upload_folder + "/" + idno + ".png"
    ok: bool = addrecord('students', idno=idno, lastname=lastname, firstname=firstname,
                         course=course, level=level, image=image)
    if not ok:
        return "Could not save the student.", 500

    file.save(image)
    return "OK", 200


@app.route("/update", methods=['POST'])
def update() -> None:
    idno: str = (request.form.get('idno') or '').strip()
    lastname: str = (request.form.get('lastname') or '').strip()
    firstname: str = (request.form.get('firstname') or '').strip()
    course: str = (request.form.get('course') or '').strip()
    level: str = (request.form.get('level') or '').strip()

    if idno.isalnum() and lastname and firstname and course and level:
        if len(getrecord('students', idno=idno)) > 0:
            updaterecord('students', idno=idno, lastname=lastname,
                         firstname=firstname, course=course, level=level)
    return redirect(url_for('main'))


@app.route("/student/<idno>")
def student(idno: str) -> None:
    rec: list = getrecord('students', idno=idno)
    if not rec:
        return render_template('student.html', s=None), 404
    s = rec[0]
    return render_template('student.html', s=s,
                           course=COURSES.get(str(s['course']).lower(), str(s['course']).upper()),
                           level=LEVELS.get(str(s['level']), s['level']))


@app.route("/delete/<idno>")
def delete(idno: str) -> None:
    rec: list = getrecord('students', idno=idno)
    deleterecord('students', idno=idno)
    if rec and rec[0]['image'] and os.path.exists(rec[0]['image']):
        os.remove(rec[0]['image'])
    return redirect(url_for('main'))


def startup_message(self) -> None:
    print(" * Running on http://127.0.0.1:%s" % self.port)
    if self.host == "0.0.0.0":
        addrs = [SERVER_ADDRESS] if SERVER_ADDRESS else lan_ips()
        for ip in addrs:
            print(" * Phone address:  http://%s:%s/main" % (ip, self.port))
        if not addrs:
            print(" * No phone address found (looked for %s*). Set SERVER_ADDRESS in app.py." % (ALLOW_PHONES and ALLOWED_PREFIX or ""))


BaseWSGIServer.log_startup = startup_message


if __name__ == "__main__":
    app.run(host="0.0.0.0" if ALLOW_PHONES else "127.0.0.1", port=5000,
            debug=True, use_debugger=False)
