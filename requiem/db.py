import os
import sqlite3
import json

INDEX_FILE_NAME = 'index.json'

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

    _link_order = None
    _requirement_order = None
    _metadata_order = None

    def __init__(self, database_path):
        self._database_path = database_path
        self._link_order = 1
        self._requirement_order = 1
        self._metadata_order  = 1

        self._initialize_sqlite()
        self._read_index()
        self._read_requirement_sets()

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
        for requirement_set in index.get('requirement_sets'):
            statement = 'INSERT INTO requirement_sets (id, name, filename) VALUES (:id, :name, :filename);'
            self._cursor.execute(statement, requirement_set)

    def insert_link(self, from_requirement_set_id, from_requirement_id, to_requirement_set_id, to_requirement_id):
        statement = """
        INSERT INTO links (
            from_requirement_set_id, 
            from_requirement_id, 
            to_requirement_set_id, 
            to_requirement_id,
            placement_order
        ) 
        VALUES (
           :from_requirement_set_id, 
           :from_requirement_id, 
           :to_requirement_set_id, 
           :to_requirement_id,
           :placement_order
        )
        ON CONFLICT DO NOTHING;
        """
        args = {
            'from_requirement_set_id': from_requirement_set_id,
            'from_requirement_id': from_requirement_id,
            'to_requirement_set_id': to_requirement_set_id,
            'to_requirement_id': to_requirement_id,
            'placement_order': self.get_link_number()
        }
        return self._cursor.execute(statement, args)

    def insert_requirement(self, set_id, requirement_id, contents):
        statement = """
        INSERT INTO requirements (requirement_set_id, requirement_id, key, value, placement_order)
        VALUES (:set_id, :req_id, :key, :value, :placement_order);
        """
        args = {
            'set_id': set_id,
            'req_id': requirement_id,
            'key': 'contents',
            'value': contents,
            'placement_order': self.get_requirement_number()
        }

        self._cursor.execute(statement, args)

    def insert_requirement_set_metadata(self, requirement_set_id, key, value):
        statement = """
        INSERT INTO requirement_set_metadata (requirement_set_id, key, value, placement_order)
        VALUES (:requirement_set_id, :key, :value, :placement_order);
        """
        args = {
            'requirement_set_id': requirement_set_id,
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
                    self.insert_link(set_id, requirement.get('id'), to_requirement_set_id, to_requirement_id)

                for link in requirement.get('to_links'):
                    from_requirement_set_id, from_requirement_id = link.split(':')
                    self.insert_link(from_requirement_set_id, from_requirement_id, set_id, requirement.get('id'))

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
