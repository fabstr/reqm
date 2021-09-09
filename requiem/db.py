import sys
import os
import sqlite3
import json
import subprocess
from pprint import pprint

INDEX_FILE_NAME = 'index.json'


def get_database_path():
    if len(sys.argv) < 2:
        raise ValueError('Usage: requiem path/to/database/directory')
    return os.path.join(
            os.path.dirname(sys.argv[0]),
            sys.argv[1])


def get_schema_file():
        filename = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                'schema.sql')
        with open(filename) as f:
            return f.read()

class Database:
    _database_path = None

    _sqlite_connection = None
    _cursor = None

    _set_order = None
    _link_order = None
    _requirement_order = None
    _metadata_order = None

    def __init__(self, database_path=None):
        if not database_path:
            database_path = get_database_path()

        self._database_path = database_path
        self._set_order = 1
        self._link_order = 1
        self._requirement_order = 1
        self._metadata_order  = 1

        self._initialize_sqlite()
        self._read_index()
        self._read_requirement_sets()

    def get_set_number(self):
        number = self._set_order
        self._set_order = self._set_order + 1
        return number

    def get_link_number(self):
        number = self._link_order
        self._link_order = self._link_order + 1
        return number

    def get_requirement_number(self):
        number = self._requirement_order
        self._requirement_order = self._requirement_order + 1
        return number

    def get_metadata_number(self):
        number = self._metadata_order
        self._metadata_order = self._metadata_order + 1
        return number

    def _initialize_sqlite(self):
        self._sqlite_connection = sqlite3.connect(':memory:')
        self._cursor = self._sqlite_connection.cursor()
        self._cursor.executescript(get_schema_file())

    def _read_index(self):
        index_filename = os.path.join(self._database_path, INDEX_FILE_NAME)
        with open(index_filename) as f:
            index = json.load(f)
        for req_set in index.get('requirement_sets'):
            self.insert_requirement_set(req_set.get('id'), req_set.get('name'), req_set.get('filename'), save=False)

    def insert_requirement_set(self, set_id, name, filename, save=True):
        statement = """
        INSERT INTO requirement_sets (id, name, filename, placement_order)
        VALUES (:id, :name, :filename, :placement_order)
        """
        args = {
                'id': set_id,
                'name': name,
                'filename': filename,
                'placement_order': self.get_set_number()
        }
        self._cursor.execute(statement, args)
        if save:
            self.save('Add requirment set {} {}'.format(set_id, name))

    def insert_link(self, from_requirement_set_id, from_requirement_id, to_requirement_set_id, to_requirement_id, save=True):
        statement = """
        INSERT INTO links (
            from_set_id, 
            from_id, 
            to_set_id, 
            to_id,
            placement_order
        ) 
        VALUES (
           :from_set_id, 
           :from_id, 
           :to_set_id, 
           :to_id,
           :placement_order
        )
        ON CONFLICT DO NOTHING;
        """
        args = {
            'from_set_id': from_requirement_set_id,
            'from_id': from_requirement_id,
            'to_set_id': to_requirement_set_id,
            'to_id': to_requirement_id,
            'placement_order': self.get_link_number()
        }
        if save:
            self.save('Add link from {}:{} to {}:{}'.format(
                from_req_set_id, from_req_id, to_req_set_id, to_req_id))

        self._cursor.execute(statement, args)

    def insert_requirement(self, set_id, requirement_id, contents):
        statement = """
        INSERT INTO requirements (set_id, id, key, value, placement_order)
        VALUES (:set_id, :id, :key, :value, :placement_order);
        """
        args = {
            'set_id': set_id,
            'id': requirement_id,
            'key': 'contents',
            'value': contents,
            'placement_order': self.get_requirement_number()
        }

        self._cursor.execute(statement, args)

    def insert_requirement_set_metadata(self, set_id, key, value):
        statement = """
        INSERT INTO requirement_set_metadata (id, key, value, placement_order)
        VALUES (:id, :key, :value, :placement_order);
        """
        args = {
            'id': set_id,
            'key': key,
            'value': value,
            'placement_order': self.get_metadata_number()
        }
        self._cursor.execute(statement, args)

    def _read_requirement_sets(self):
        self._cursor.execute('SELECT id, name, filename from requirement_sets')
        link_insert_order = 1

        for index_entry in self._cursor.fetchall():
            (set_id, name, filename) = index_entry

            with open(os.path.join(self._database_path, filename)) as f:
                requirement_set = json.load(f)

            # read requirements
            for requirement in requirement_set.get('requirements'):
                self.insert_requirement(set_id, requirement.get('id'), requirement.get('contents'))

                # links
                for link in requirement.get('from_links'):
                    to_requirement_set_id, to_requirement_id = link.split(':')
                    self.insert_link(set_id, requirement.get('id'), to_requirement_set_id, to_requirement_id, save=False)

                for link in requirement.get('to_links'):
                    from_requirement_set_id, from_requirement_id = link.split(':')
                    self.insert_link(from_requirement_set_id, from_requirement_id, set_id, requirement.get('id'), save=False)

            # read metadata
            for key, value in requirement_set.items():
                if key == 'requirements':
                    continue
                self.insert_requirement_set_metadata(set_id, key, value)

    def get_requirement_sets(self):
        statement = 'SELECT id, name, filename FROM requirement_sets;'
        self._cursor.execute(statement)
        sets = []
        for req_set in self._cursor.fetchall():
            (set_id, name, filename) = req_set
            sets.append({
                'id': set_id,
                'name': name,
                'filename': filename
            })
        return sets

    def get_requirement_set(self, set_id):
        statement = 'SELECT id, name, filename FROM requirement_sets WHERE id = :set_id;'
        self._cursor.execute(statement, {'set_id': set_id})
        for req_set in self._cursor.fetchall():
            (set_id, name, filename) = req_set
            return {
                'id': set_id,
                'name': name,
                'filename': filename
            }
        return None

    def get_links_with_content(self, set_id, req_id):
        statement = """
        SELECT links.from_set_id, links.from_id, links.to_set_id, links.to_id,
            r_from.key, r_from.value, r_to.key, r_to.value
        FROM links
        JOIN requirements AS r_from ON (links.from_set_id = r_from.set_id AND links.from_id = r_from.id)
        JOIN requirements AS r_to ON (links.to_set_id = r_to.set_id AND links.to_id = r_to.id)
        WHERE ( 
                (links.from_set_id = :set_id AND links.from_id = :req_id)
                OR 
                (links.to_set_id = :set_id AND links.to_id = :req_id)
            )
        AND r_from.key = 'contents' 
        AND r_to.key = 'contents'
        ORDER BY links.placement_order ASC;
        """
        self._cursor.execute(statement, {'set_id': set_id, 'req_id': req_id})
        return [
                {
                    'from_set_id': from_set_id,
                    'from_id': from_id,
                    'from_content': from_value,
                    'to_set_id': to_set_id,
                    'to_id': to_id,
                    'to_content': to_value
                }
                for (from_set_id, from_id, to_set_id, to_id, from_key, from_value, to_key, to_value)
                in self._cursor.fetchall()
        ]

    def get_requirements(self, set_id, with_link_contents=False):
        requirements = []

        statement = """
        SELECT id, key, value 
        FROM requirements 
        WHERE set_id = :set_id
        ORDER BY placement_order ASC
        """
        self._cursor.execute(statement, {'set_id': set_id})

        current_id = None
        requirement = {}
        rows = self._cursor.fetchall()

        for row in rows:
            (req_id, key, value) = row
            if current_id != None and current_id != req_id:
                requirements.append(requirement)
                current_id = req_id
                requirement = {}

            current_id = req_id

            requirement['id'] = req_id
            requirement[key] = value

            links = self.get_links_with_content(set_id, req_id)
            requirement['from_links'] = [
                '{}:{}'.format(link.get('to_set_id'), link.get('to_id'))
                for link in links if link.get('from_id') == req_id
            ]
            requirement['to_links'] = [
                '{}:{}'.format(link.get('from_set_id'), link.get('from_id'))
                for link in links if link.get('to_id') == req_id
            ]

            if with_link_contents:
                raise NotImplementedError('links with contents not implemented yet')
                requirement['to_link_contents'] = {}

        # when there are no requirments in the set we don't want to add an empty
        # dict
        if len(requirement) > 0:
            requirements.append(requirement)

        return requirements

    def remove_requirement(self, set_id, req_id, save=True):
        statement = 'DELETE FROM requirements WHERE set_id = :set_id AND id = :req_id'
        self._cursor.execute(statement, {'set_id': set_id, 'req_id': req_id})
        if save:
            self.save('Remove requirement {}'.format(req_id))


    def update_requirement(self, set_id, req_id, contents, save=True):
        statement = 'UPDATE requirements SET value=:value WHERE set_id=:set_id AND id=:req_id AND key=:key'
        self._cursor.execute(statement, {'set_id': set_id, 'req_id': req_id, 'key': 'contents', 'value': contents})
        if save:
            self.save('Update requirement {}'.format(req_id))

    
    # This function is a bit tricky and it's very likely the exact numbering of 
    # the placement_order is not continuous. However, what do matters is that 
    # the placement order is strictly increasing so that it can be used to  sort
    # the requirements. This holds for this implementation of the movement.
    # Also, the specific placement older numbers do not matter as they only 
    # exist in the in-memory database.
    def move_requirement(self, set_id, req_id, new_index, placement_order=None, save=True):
        # first find old placement_order
        statement = 'SELECT placement_order FROM requirements WHERE set_id = :set_id and id = :req_id'
        self._cursor.execute(statement, {'set_id': set_id, 'req_id': req_id})
        old_placement_order = self._cursor.fetchone()[0]

        if placement_order:
            new_placement_order = placement_order
        else:
            # find the first placement order in the set, can then calculate the new placement order
            # since new_index is the same as the offset from the beginning of the set
            statement = 'SELECT placement_order FROM requirements WHERE set_id = :set_id ORDER BY placement_order ASC LIMIT 1'
            self._cursor.execute(statement, {'set_id': set_id, 'req_id': req_id})
            first_placement_order = self._cursor.fetchone()[0]
            new_placement_order = first_placement_order + new_index

        if old_placement_order < new_placement_order:
            # moved down
            # move all requirements before the new placement_order up one step
            # move all requirements after new_placement_order down one step
            statement = 'UPDATE requirements SET placement_order = placement_order - 1 WHERE placement_order <= :new_placement_order'
            self._cursor.execute(statement, {'new_placement_order': new_placement_order})
            statement = 'UPDATE requirements SET placement_order = placement_order + 1 WHERE placement_order > :new_placement_order'
            self._cursor.execute(statement, {'new_placement_order': new_placement_order})
        else:
            # moved up
            # move all requirements at or after new_placement_order
            statement = 'UPDATE requirements SET placement_order = placement_order + 1 WHERE placement_order >= :new_placement_order'
            self._cursor.execute(statement, {'new_placement_order': new_placement_order})

        # move the requirement to its new position
        statement = 'UPDATE requirements SET placement_order = :new_placement_order WHERE set_id = :set_id and id = :req_id'
        self._cursor.execute(statement, {'new_placement_order': new_placement_order, 'set_id': set_id, 'req_id': req_id})

        if save:
            self.save(comment='Move requirement {} to index {}'.format(req_id, new_index))

    def find_requirement_placement_order(self, set_id, req_id):
        statement = 'SELECT placement_order FROM requirements WHERE set_id = :set_id and id = :req_id'
        self._cursor.execute(statement, {'set_id': set_id, 'req_id': req_id})
        placement_order = self._cursor.fetchone()[0]
        return placement_order

    def save(self, comment):
        # save index
        statement = 'SELECT id, name, filename FROM requirement_sets ORDER BY placement_order ASC'
        self._cursor.execute(statement)
        index = []
        for row in self._cursor.fetchall():
            (set_id, name, filename) = row
            index.append({
                'id': set_id,
                'name': name,
                'filename': filename
            })
        with open(os.path.join(self._database_path, INDEX_FILE_NAME), 'w') as f:
            json.dump({'requirement_sets': index}, f, indent=4, sort_keys=True)
        subprocess.run(['git', 'add', INDEX_FILE_NAME], cwd=self._database_path)
        
        # save requirement sets
        for req_set in index:
            requirements = self.get_requirements(req_set.get('id'))
            data = {
                'name': req_set.get('name'),
                'id': req_set.get('id'),
                'requirements': requirements
            }
            with open(os.path.join(self._database_path, req_set.get('filename')), 'w') as f:
                json.dump(data, f, indent=4, sort_keys=True)

            subprocess.run(['git', 'add', req_set.get('filename')], cwd=self._database_path)

        subprocess.run(['git', 'commit', '-m', comment], cwd=self._database_path)
