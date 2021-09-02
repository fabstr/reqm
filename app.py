import json
import os
import uuid
from flask import Flask, render_template, send_from_directory, url_for, request

app = Flask(__name__)

def get_index_file():
    with open('database/index.json') as f:
        index = json.load(f)
        return index

def get_requirement_set_filename(set_id):
    for set in get_index_file().get('requirement_sets'):
        if set.get('id') == set_id:
            return os.path.join('database', set.get('name') + '.json')

    return None

def get_requirement_set_by_id(set_id):
    filename = get_requirement_set_filename(set_id)
    if filename:
        with open(filename) as f:
            return json.load(f)

def save_requirement_set_by_id(set_id, requirement_set):
    filename = get_requirement_set_filename(set_id)
    print(filename)
    if not filename:
        return None

    with open(filename, 'w') as f:
        json.dump(requirement_set, f, indent=4)

def make_requirement(contents, from_links=[], to_links=[]):
    return {
        'id': str(uuid.uuid4()),
        'contents': contents,
        'from_links': from_links,
        'to_links': to_links
    }


@app.route('/')
def get_index():
    index = get_index_file()

    sets = index.get('requirement_sets')
    return render_template('index.html', requirement_sets=[
            {
                'url': url_for('requirement_set', id=s.get('id')),
                'name': s.get('name')
            }
            for s in sets
    ])


@app.route('/requirement_set/<id>')
def requirement_set(id=None):
    requirement_set = get_requirement_set_by_id(id)
    if requirement_set:
        return render_template('requirements.html', requirement_set=requirement_set)
    else:
        return "Error!"

@app.route('/requirement_set/<set_id>/<req_id>', methods=['POST'])
def save_requirement(set_id, req_id):
    requirement_set = get_requirement_set_by_id(set_id)
    if not requirement_set:
        return {'status': 'error'}, 404

    for value in requirement_set.get('requirements'):
        if value.get('id') == req_id:
            requirement = request.get_json()
            value['contents'] = requirement.get('contents')
    save_requirement_set_by_id(set_id, requirement_set)
    return {'saved': True}

@app.route('/requirement_set/<set_id>/<req_id>/move', methods=['POST'])
def move_requirement(set_id, req_id):
    requirement_set = get_requirement_set_by_id(set_id)
    if not requirement_set:
        return {'status': 'error'}, 404

    index = request.get_json().get('index')

    for idx, value in enumerate(requirement_set.get('requirements')):
        if value.get('id') == req_id:
            requirement_set.get('requirements').remove(value)
            break

    requirement_set.get('requirements').insert(index, value)
    save_requirement_set_by_id(set_id, requirement_set)
    return {'saved': True}

@app.route('/requirement_set/<set_id>/add', methods=['POST'])
def add_requirement(set_id):
    requirement_set = get_requirement_set_by_id(set_id)
    if not requirement_set:
        return {'status': 'error'}, 404

    data = request.get_json()
    requirement = data.get('requirement')
    if data.get('before') != '':
        pass
    if data.get('after') != '':
        pass
    else:
        requirement_set.get('requirements').append(make_requirement(requirement.get('contents')))

    save_requirement_set_by_id(set_id, requirement_set)
    return {'saved': True}

@app.route('/link', methods=['POST'])
def link():
    data = request.get_json()
    from_req_set_id = data.get('from').get('requirement_set')
    from_req_id = data.get('from').get('id')
    to_req_set_id = data.get('to').get('requirement_set')
    to_req_id = data.get('to').get('id')

    from_requirement_set = get_requirement_set_by_id(from_req_set_id)
    to_requirement_set = get_requirement_set_by_id(to_req_set_id)

    combined_from_link = from_req_set_id + ':' + from_req_id
    combined_to_link = to_req_set_id + ':' + to_req_id

    # find from requirement, add to link
    for r in from_requirement_set.get('requirements'):
        if r.get('id') == from_req_id:
            if combined_to_link not in r.get('to_links'):
                r.get('to_links').append(combined_to_link)

    for r in to_requirement_set.get('requirements'):
        if r.get('id') == to_req_id:
            if combined_from_link not in r.get('from_links'):
                r.get('from_links').append(combined_from_link)

    save_requirement_set_by_id(from_req_set_id, from_requirement_set)
    save_requirement_set_by_id(to_req_set_id, to_requirement_set)

    if not requirement_set:
        return {'status': 'error'}, 404

    return {'saved': True}

@app.route('/static/bootstrap.min.css')
def get_bootstrap_css():
    return send_from_directory('static', 'bootstrap.min.css')

@app.route('/static/bootstrap.bundle.min.js')
def get_bootstrap_js():
    return send_from_directory('static', 'bootstrap.bundle.min.js')

@app.route('/static/js.min.js')
def get_js_js():
    return send_from_directory('static', 'js.js')

