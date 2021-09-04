import subprocess
import re
import sys
import json
import os
import uuid
import markdown
from flask import url_for

INDEX_FILE_NAME = 'index.json'


def get_requirement_sets(with_requirements=True):
    index = get_index_file()
    sets = index.get('requirement_sets')
    return [
            {
                'id': s.get('id'),
                'url': url_for('requirement_set', set_id=s.get('id')),
                'name': s.get('name'),
                'canremove': False,
                'requirements': RequirementSet.get_by_id(s.get('id')).get_requirements(with_html=True) if with_requirements else []
            }
            for s in sets
    ]

def get_database_path():
    if len(sys.argv) < 2:
        raise ValueError('Usage: requiem path/to/database/directory')
    return os.path.join(
            os.path.dirname(sys.argv[0]),
            sys.argv[1])

def get_index_file():
    indexfile = os.path.join(get_database_path(), INDEX_FILE_NAME)
    with open(indexfile) as f:
        index = json.load(f)
        return index

def get_requirement_set_filename(set_id):
    for set in get_index_file().get('requirement_sets'):
        if set.get('id') == set_id:
            return os.path.join(get_database_path(), set.get('name') + '.json')

    return None

def make_requirement(contents, from_links=[], to_links=[]):
    return {
        'id': str(uuid.uuid4()),
        'contents': contents,
        'from_links': from_links,
        'to_links': to_links
    }

def is_database(path):
    git = os.path.join(path, '.git')
    index = os.path.join(path, INDEX_FILE_NAME)
    return os.path.isdir(path) and os.path.isdir(git) and os.path.exists(index)

def initialise_database(path):
    print('Initializing database')

    if not os.path.isdir(path):
        print('Directory doesn\'t exist, creating {}'.format(path))
        os.mkdir(path)

    indexfile = os.path.join(path, INDEX_FILE_NAME)
    index = {
            'requirement_sets': []
    }

    print('Writing index {}'.format(indexfile))
    with open(indexfile, 'w') as f:
        json.dump(index, f, indent=4)

    print('Running git init, add and commit')
    subprocess.run(['git', 'init'], cwd=path)
    subprocess.run(['git', 'add', INDEX_FILE_NAME], cwd=path)
    subprocess.run(['git', 'commit', '-m', 'Initialise database'], cwd=path)
    print('Database initialised')


def add_requirement_set(name, set_id):
    database_path = get_database_path()

    if not re.match(r'[A-Za-z0-9_ -]+', name):
        raise ValueError('Invalid requirement set name \'{}\'. Valid characters are: space, underscore, dash, A-Z, a-z, and 0-9.'.format(name))

    requirement_set_filename = '{}.json'.format(name)
    requirement_set = {
        'name': name,
        'id': set_id,
        'requirements': []
    }

    index_entry = {
        'id': set_id,
        'name': name,
        'filename': requirement_set_filename
    }

    # add it to the index
    with open(os.path.join(database_path, INDEX_FILE_NAME)) as f:
        index = json.load(f)
    for r in index.get('requirement_sets'):
        if r.get('id') == set_id:
            raise ValueError('Requirement set id {} already exists.'.format(set_id))
    index.get('requirement_sets').append(index_entry)
    with open(os.path.join(database_path, INDEX_FILE_NAME), 'w') as f:
        json.dump(index, f, indent=4)

    # add the requirement set file
    with open(os.path.join(database_path, requirement_set_filename), 'w') as f:
        json.dump(requirement_set, f, indent=4)

    subprocess.run(['git', 'add', INDEX_FILE_NAME, requirement_set_filename], cwd=database_path)
    subprocess.run(['git', 'commit', '-m', 'Create requirement set {}'.format(name)], cwd=database_path)

class RequirementSet:
    _requirement_set = None
    _database_path = None
    _filename = None

    def __init__(self, database_path, filename):
        self._database_path = database_path
        self._filename = filename
        with open(os.path.join(self._database_path, self._filename)) as f:
            self._requirement_set = json.load(f)

    def get_requirements(self, with_html=False):
        if with_html:
            for requirement in self._requirement_set.get('requirements'):
                requirement['html'] = markdown.markdown(requirement.get('contents'))

        return self._requirement_set

    def get_by_id(requirement_set_id):
        for req_set in get_index_file().get('requirement_sets'):
            if req_set.get('id') == requirement_set_id:
                return RequirementSet(get_database_path(), req_set.get('filename'))

        raise ValueError('Requirement set with id {} not found.'.format(requirement_set_id))



    def move_requirement(self, requirement_id, index):
        for idx, value in enumerate(self._requirement_set.get('requirements')):
            if value.get('id') == requirement_id:
                self._requirement_set.get('requirements').remove(value)
                break

        self._requirement_set.get('requirements').insert(index, value)
        self.save(comment='Move requirement {} to index {}'.format(requirement_id, index))

    def remove_requirement(self, requirement_id):
        for idx, value in enumerate(self._requirement_set.get('requirements')):
            if value.get('id') == requirement_id:
                self._requirement_set.get('requirements').remove(value)

        self.save(comment='Remove requirement {}'.format(requirement_id))

    def update_requirement(self, requirement_id, contents):
        for value in self._requirement_set.get('requirements'):
            if value.get('id') == requirement_id:
                value['contents'] = contents
                break
        self.save(comment='Update requirement {}'.format(requirement_id))

    def add_requirement(self, contents, before=None, after=None):
        new_requrement = make_requirement(contents)

        index = None
        if before:
            for idx, value in enumerate(self._requirement_set.get('requirements')):
                if value.get('id') == before:
                    index = idx
                    break

        if after:
            for idx, value in enumerate(self._requirement_set.get('requirements')):
                if value.get('id') == after:
                    index = idx + 1
                    break
        if not before and not after:
            index = len(self._requirement_set.get('requirements'))

        if index == None:
            raise ValueError('Could not find requirement, before={}, after={}'.format(before, after))

        self._requirement_set.get('requirements').insert(index, new_requrement)

        if before != '' or after != '':
            indexmsg = ' at index {}'.format(index)
        else:
            indexmsg = ''
        self.save('Add new requirement {}{}'.format(new_requrement.get('id'), indexmsg))
      

        return new_requrement.get('id')

    def add_from_link(self, requirement_id, to_id):
        # link from a requirement in this set to another
        for r in self._requirement_set.get('requirements'):
            if r.get('id') == requirement_id:
                if to_id not in r.get('from_links'):
                    r.get('from_links').append(to_id)
        self.save('Add link from {} to {}'.format(requirement_id, to_id))

    def add_to_link(self, requirement_id, from_id):
        # link to a requirement in this set from another
        for r in self._requirement_set.get('requirements'):
            if r.get('id') == requirement_id:
                if from_id not in r.get('to_links'):
                    r.get('to_links').append(from_id)
        self.save('Add link to {} from {}'.format(requirement_id, from_id))

    def save(self, comment=None, tag=None):
        filename = os.path.join(self._database_path, self._filename)
        with open(filename, 'w') as f:
            json.dump(self._requirement_set, f, indent=4)

        if comment:
            subprocess.run(['git', 'add', self._filename], cwd=self._database_path)
            subprocess.run(['git', 'commit', '-m', comment], cwd=self._database_path)

        if tag:
            print('WARNING! tag not implemented yet')

    def metadata(self):
        return {
            'Title': self._requirement_set.get('name')
        }

    def export(self, target='markdown'):
        text = '\n'.join([r.get('contents') + '\n' for r in self._requirement_set.get('requirements')])
        if target == 'markdown':
            return text
        if target == 'html':
            return markdown.markdown(text)
        else:
            raise ValueError('Unknown export target {}'.format(target))
