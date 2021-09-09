import sqlite3
import subprocess
import re
import sys
import json
import os
import uuid
import markdown
from pprint import pprint
from flask import url_for
from .db import Database

INDEX_FILE_NAME = 'index.json'




def get_requirement_sets(database, with_requirements=False):
    return [
            {
                'id': s.get('id'),
                'url': url_for('requirement_set', set_id=s.get('id')),
                'name': s.get('name'),
                'canremove': False,
                'requirements': RequirementSet(database, s.get('id')).get_requirements(with_html=True) if with_requirements else []
            }
            for s in database.get_requirement_sets()
    ]


def get_index_file():
    indexfile = os.path.join(get_database_path(), INDEX_FILE_NAME)
    with open(indexfile) as f:
        index = json.load(f)
        return index

def make_requirement(contents):
    return {
        'id': str(uuid.uuid4()),
        'contents': contents
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


# TODO
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
    _set_id = None
    _database = None

    def __init__(self, database, set_id):
        self._database = database
        self._set_id = set_id

    def get_requirements(self, with_html=False):
        requirement_set = self._database.get_requirement_set(self._set_id)
        requirement_set['requirements'] = self._database.get_requirements(self._set_id)

        if with_html:
            for requirement in requirement_set.get('requirements'):
                requirement['html'] = markdown.markdown(requirement.get('contents'))

        return requirement_set

    def move_requirement(self, requirement_id, index):
        self._database.move_requirement(self._set_id, requirement_id, index)

    def remove_requirement(self, requirement_id):
        self._database.remove_requirement(self._set_id, requirement_id)


    def update_requirement(self, requirement_id, contents):
        self._database.update_requirement(self._set_id, requirement_id, contents)

    def add_requirement(self, contents, before=None, after=None):
        new_requirement = make_requirement(contents)

        placement_order = None
        if before:
            placement_order = self._database.find_requirement_placement_order(self._set_id, before)
        elif after:
            placement_order = self._database.find_requirement_placement_order(self._set_id, after) + 1

        self._database.insert_requirement(self._set_id, new_requirement.get('id'), new_requirement.get('contents'))

        if before or after:
            self._database.move_requirement(self._set_id, new_requirement.get('id'), new_index=None, placement_order=placement_order, save=False)

        self._database.save('Add new requirement {}'.format(new_requirement.get('id')))

        return new_requirement.get('id')

    # TODO
    def metadata(self):
        return {
            'Title': self.get_requirements().get('name')
        }

    def export(self, target='markdown'):
        text = '\n'.join([
            r.get('contents') + '\n' 
            for r in self.get_requirements().get('requirements')
        ])
        if target == 'markdown':
            return text
        if target == 'html':
            return markdown.markdown(text)
        else:
            raise ValueError('Unknown export target {}'.format(target))
