import os
import re
import urllib
import requests
import xlrd

from flask import Flask, request, abort
from flask.json import jsonify
from bs4 import BeautifulSoup

app = Flask(__name__)

weeks = ('lu', 'ma', 'me', 'je', 've', 'sa', 'di')
wdict = {key: value for (value, key) in enumerate(weeks)}
is_week = r'^\s*(' + '|'.join(weeks) + ')\s+\d{2}.\d{2}\s'


@app.route('/groople-doc', methods=['POST'])
def groople_doc():

    event = request.form['event']
    username = request.form['username']
    password = request.form['password']
    document = request.form['document']

    app.logger.debug("Connecting to Groople")
    s = requests.Session()

    r = s.get("https://app.groople.me")

    soup = BeautifulSoup(r.content, 'html.parser')
    forms = soup.find_all('form')
    if len(forms) <= 0:
        abort(501)

    params = {
        "username": username,
        "password": password,
    }
    for i in forms[0].find_all("input", type="hidden"):
        params[i["name"]] = i["value"]

    for i in forms[0].find_all("input", type="submit"):
        params[i["name"]] = i["value"]

    app.logger.debug("Login to Groople")
    r = s.post('https://app.groople.me/login.htm', data=params)

    q = urllib.parse.parse_qs(urllib.parse.urlparse(r.url).query)
    app.logger.debug("D {0}".format(q['p']))

    if q['p'][0] != "loginok":
        abort(401)

    # Fetch document
    params = {
        'org': str(q['org'][0]),
        'event': str(event),
        'document': str(document),
        'format': 'xls',
        'osid': str(q['osid'][0]),
    }

    r = s.get("https://app.groople.me/admin/docdisplay.htm", stream=True, params=params)

    if len(r.content) <= 0:
        abort(503)

    # read Excel document
    book = xlrd.open_workbook(file_contents=r.content)
    sheet = book.sheet_by_index(0)
    app.logger.debug("Sheet name: {0}".format(sheet.name))

    header = [i.value for i in sheet.row(0)]
    h_map = {key: value for (value, key) in enumerate(header)}

    week_no = 0
    prev_day_no = -1
    week_map = dict()
    for i, x in enumerate(header):
        m = re.match(is_week, x)
        if m:
            day_no = wdict.get(m.group(1).lower(), -1)
            if day_no < prev_day_no:
                week_no += 1

            week_map[i] = week_no
            prev_day_no = day_no

    app.logger.debug("h_map : {0}".format(h_map))
    app.logger.debug("week_map : {0}".format(week_map))

    result = list()
    for i in range(1, sheet.nrows):
        record = [i.value for i in sheet.row(i)]
        out = [record[h_map[i]] for i in [
            "Participant's username",
            "First name",
            "Last name",
            "E-mail address",
            "Tel parent 1",
            "Tel parent 2",
            "Nombre de passeports payés",
        ]]

        used = [0 for i in range(week_no + 1)]
        for j in week_map.keys():
            if not re.match(r"x{3}", record[j], re.IGNORECASE):
                used[week_map[j]] = 1

        result.append([out, used])

    return jsonify(data=result)


if __name__ == '__main__':
    debug = os.getenv("DEBUG", None)
    if debug is not None:
        app.logger.setLevel('DEBUG')

    app.run(port=8888, debug=debug is not None)
