SCHOOL - student registration (Flask + SQLite)

RUN
  pip install flask
  python app.py
  open http://127.0.0.1:5000/main

By default the site runs only on this computer (ALLOW_PHONES = False at the top of app.py).
The QR codes then hold a 127.0.0.1 link, which opens on this computer (click the link under the
QR in the pencil pop-up to see the student's picture and details).

TO LET A PHONE SCAN THE QR (optional)
  Set ALLOW_PHONES = True in app.py and restart. Then:
  1. Phone and computer must be on the SAME network, with the phone's mobile data off.
  2. python app.py prints "Phone address". Type it in the phone's browser first.
  3. The QR only uses addresses starting with ALLOWED_PREFIX (172.17.16.); set it to "" for any.
     If your address is not found, type it in SERVER_ADDRESS.
  4. "Unreachable" = phone cannot find the computer (different network / Wi-Fi blocks devices;
     try the phone's hotspot). "Took too long" = Windows Firewall: Windows Security > Firewall >
     Allow an app through firewall > Python > tick Private and Public.
