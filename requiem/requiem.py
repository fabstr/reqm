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

def rename_requirement_set(set_id, new_name, old_name):
    if not validate_name(new_name) or not validate_name(old_name):
        raise ValueError('Invalid requirement set name \'{}\'. Valid characters are: space, underscore, dash, A-Z, a-z, and 0-9.'.format(name))

    filename = '{}.json'.format(new_name)
    old_filename = '{}.json'.format(old_name)
    database = Database()
    database.rename_requirement_set(set_id, new_name, filename, old_filename)

def validate_name(name):
    return re.match(r'[A-Za-z0-9_ -]+', name)


def add_requirement_set(name, set_id):
    if not validate_name(name):
        raise ValueError('Invalid requirement set name \'{}\'. Valid characters are: space, underscore, dash, A-Z, a-z, and 0-9.'.format(name))

    filename = '{}.json'.format(name)
    database = Database()
    database.insert_requirement_set(set_id, name, filename, save=True)

class RequirementSet:
    _set_id = None
    _database = None

    def __init__(self, database, set_id):
        self._database = database
        self._set_id = set_id

    def get_requirements(self, with_html=False, with_link_contents=False):
        requirement_set = self._database.get_requirement_set(self._set_id)
        requirement_set['requirements'] = self._database.get_requirements(self._set_id)

        if with_html:
            for requirement in requirement_set.get('requirements'):
                if requirement:
                    requirement['html'] = markdown.markdown(requirement.get('contents'))

        if with_link_contents:
            print("hej")
            for requirement in requirement_set.get('requirements'):
                for key, val in enumerate(requirement.get('to_links')):
                    (set_id, req_id) = val.split(':')
                    linked_requirement = self._database.get_requirement(set_id, req_id)
                    if with_html:
                        linked_requirement['contents'] = markdown.markdown(linked_requirement.get('contents'))
                    requirement.get('to_links')[key] = linked_requirement
                for key, val in enumerate(requirement.get('from_links')):
                    (set_id, req_id) = val.split(':')
                    linked_requirement = self._database.get_requirement(set_id, req_id)
                    if with_html:
                        linked_requirement['contents'] = markdown.markdown(linked_requirement.get('contents'))
                    requirement.get('from_links')[key] = linked_requirement

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
        def show_details(r):
            return not re.match(r'^\s*#', r.get('contents'))

        def append_link_contents(lines, link):
            (set_id, req_id) = link.split(':')
            linked_requirement = self._database.get_requirement(set_id, req_id)
            contents = linked_requirement.get('contents')
            if target == 'html':
                contents = markdown.markdown(contents)
            lines.append('*{}* {}'.format(link, contents))

        def get_line(r):
            lines = []
            lines.append(r.get('contents'))
            if show_details(r):
                lines.append('*Id:* {}'.format(r.get('id')))
                if len(r.get('from_links')) > 0:
                    lines.append('*From links:*')
                    for link in r.get('from_links'):
                        append_link_contents(lines, link)
                if len(r.get('to_links')) > 0:
                    lines.append('*To links:*')
                    for link in r.get('to_links'):
                        append_link_contents(lines, link)
            lines.append('* * * ')
            return '\n\n'.join(lines)
        text = '\n'.join([
            get_line(r) + '\n'
            for r in self.get_requirements(with_html=False).get('requirements')
        ])
        if target == 'markdown':
            return text
        if target == 'html':
            return markdown.markdown(text)
        else:
            raise ValueError('Unknown export target {}'.format(target))
