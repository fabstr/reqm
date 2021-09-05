# Requiem

This is a proof of concept of a requirement management tool. The purpose is to 
show for myself that implementation of such a tool is not that hard and that 
existing tools may very well be much more cumbersome to use than necessary.

A core use case is that the requirements are version controlled with a commonly
use tool and the requirement files are both machine and human readable. 

Git is used as the version control tool and requirements are stored in human
readable json files.

## Development and dunning
Pipenv is used. 

To install dependencies, clone the repo and run
```bash
pipenv install
```

To run, execute (where python is run inside the pipenv shell):
```bash
pipenv shell
python app.py path/to/database/directory
```

If the database directory do not exist, Requiem will automatically create the 
directory and initialize its database. 

Please do not point to an existing non-empty directory unless it is already 
an initialized database.


