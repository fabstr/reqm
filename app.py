import sys
from requiem import requiem, db
from flask import Flask, render_template, send_from_directory, url_for, request, redirect

app = Flask(__name__)

@app.route('/')
def index():
    database = db.Database()
    return render_template('index.html', requirement_sets=requiem.get_requirement_sets(database))

@app.route('/requirement_set/<set_id>/remove', methods=['POST'])
def remove_requirement_set(set_id):
    raise NotImplementedError('Removing requirement sets is not implemented yet.')

@app.route('/requirement_set/<set_id>/rename', methods=['POST'])
def rename_requirement_set(set_id):
    new_name = request.form.get('name')
    old_name = request.form.get('old_name')
    requiem.rename_requirement_set(set_id, new_name, old_name)
    return redirect(url_for('manage_requirement_sets'))

@app.route('/requirement_set', methods=['POST'])
def add_requirement_set():
    set_name = request.form.get('name')
    set_id = request.form.get('id')
    requiem.add_requirement_set(set_name, set_id)
    return redirect(url_for('index'))

@app.route('/requirement_set/<set_id>')
def requirement_set(set_id):
    database = db.Database()
    req_set = requiem.RequirementSet(database, set_id)
    return render_template('requirements.html', 
            requirement_set=req_set.get_requirements(with_html=True),
            requirement_sets=requiem.get_requirement_sets(database, with_requirements=True)
    )

@app.route('/manage')
def manage_requirement_sets():
    database = db.Database()
    return render_template('manage.html', requirement_sets=requiem.get_requirement_sets(database))

@app.route('/requirement_set/<set_id>/markdown')
def export_requirement_set(set_id):
    database = db.Database()
    req_set = requiem.RequirementSet(database, set_id)
    text = req_set.export()
    return text, 200, {
            'Content-Type': 'text/markdown',
            'Content-Disposition': 'attachment; filename={}.md'.format(req_set.metadata().get('Title'))
    }

@app.route('/requirement_set/<set_id>/preview')
def preview_requirement_set(set_id):
    database = db.Database()
    req_set = requiem.RequirementSet(database, set_id)
    return req_set.export(target='html')

@app.route('/requirement_set/<set_id>/<req_id>', methods=['POST'])
def update_requirement(set_id, req_id):
    database = db.Database()
    req_set = requiem.RequirementSet(database, set_id)
    req_set.update_requirement(req_id, request.form.get('contents'))
    return redirect(url_for('requirement_set', set_id=set_id, _anchor=req_id))

@app.route('/requirement_set/<set_id>/<req_id>/remove', methods=['POST'])
def remove_requirement(set_id, req_id):
    database = db.Database()
    req_set = requiem.RequirementSet(database, set_id)
    req_set.remove_requirement(req_id)
    return redirect(url_for('requirement_set', set_id=set_id))

@app.route('/requirement_set/<set_id>/<req_id>/move', methods=['POST'])
def move_requirement(set_id, req_id):
    index = request.get_json().get('index')
    database = db.Database()
    req_set = requiem.RequirementSet(database, set_id)
    req_set.move_requirement(req_id, index)
    return redirect(url_for('requirement_set', set_id=set_id, _anchor=req_id))

@app.route('/requirement_set/<set_id>/add', methods=['POST'])
def add_requirement(set_id):
    before = request.form.get('before')
    after = request.form.get('after')
    contents = request.form.get('contents')

    database = db.Database()
    req_set = requiem.RequirementSet(database, set_id)
    req_id = req_set.add_requirement(contents, before=before, after=after)

    return redirect(url_for('requirement_set', set_id=set_id, _anchor=req_id))

@app.route('/link', methods=['POST'])
def link():
    direction = request.form.get('direction')
    if direction == 'to':
        from_req_set_id = request.form.get('that_requirement_set_id')
        from_req_id = request.form.get('that_requirement_id')
        to_req_set_id = request.form.get('this_requirement_set_id')
        to_req_id = request.form.get('this_requirement_id')
    elif direction == 'from':
        to_req_set_id = request.form.get('that_requirement_set_id')
        to_req_id = request.form.get('that_requirement_id')
        from_req_set_id = request.form.get('this_requirement_set_id')
        from_req_id = request.form.get('this_requirement_id')
    else:
        raise ValueError('Invalid direction {}'.format(direction))

    database = db.Database()
    database.insert_link(from_req_set_id, from_req_id, to_req_set_id, to_req_id)

    return redirect(url_for('requirement_set', 
        set_id=request.form.get('this_requirement_set_id'),
        _anchor=request.form.get('this_requirement_id')))

@app.route('/static/bootstrap.min.css')
def get_bootstrap_css():
    return send_from_directory('static', 'bootstrap.min.css')

@app.route('/static/style.css')
def get_style_css():
    return send_from_directory('static', 'style.css')

@app.route('/static/bootstrap.bundle.min.js')
def get_bootstrap_js():
    return send_from_directory('static', 'bootstrap.bundle.min.js')

@app.route('/static/js.min.js')
def get_js_js():
    return send_from_directory('static', 'js.js')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise ValueError('Usage: requiem path/to/database/directory')
    database_path = sys.argv[1]
    if not requiem.is_database(database_path):
        requiem.initialise_database(database_path)

    app.run(host='127.0.0.1', port=5000)
