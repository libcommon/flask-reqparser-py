# flask-reqparser-py

## Overview

The Flask web framework provides access to request parameters via [flask.request.args](https://flask.palletsprojects.com/en/1.1.x/api/#flask.Request.args)
for `GET` requests and via [flask.request.form](https://flask.palletsprojects.com/en/1.1.x/api/#flask.Request.form) for `PUT` and `POST` requests.
Requiring certain parameters be present for an endpoint, or parsing parameters as custom types, necessitates extra logic to process values from the aforementioned
dictionaries and is error-prone.  However, API endpoints can act much like command line interfaces, and Python has solved that problem
fairly will with the [argparse](https://docs.python.org/3/library/argparse.html) library.  `flask-reqparser-py` exposes a `RequestParser` class
that allows you to define a parser for request arguments, and access them like regular command line arguments.

## Installation

### Install from PyPi (preferred method)

```bash
pip install lc-flask-reqparser
```

### Install from GitHub with Pip

```bash
pip install git+https://github.com/libcommon/flask-reqparser-py.git@vx.x.x#egg=lc_flask_reqparser
```

where `x.x.x` is the version you want to download.

## Install by Manual Download

To download the source distribution and/or wheel files, navigate to
`https://github.com/libcommon/flask-reqparser-py/tree/releases/vx.x.x/dist`, where `x.x.x` is the version you want to install,
and download either via the UI or with a tool like wget. Then to install run:

```bash
pip install <downloaded file>
```

Do _not_ change the name of the file after downloading, as Pip requires a specific naming convention for installation files.

## Dependencies

`flask-reqparser-py` depends on, and is designed to work with, the 
[Flask framework](https://flask.palletsprojects.com/en/1.1.x/).  Only Python versions >= 3.6 are officially supported.

## Getting Started

The syntax for defining a `RequestParser` is almost identical to an `ArgumentParser`, except that all arguments should be
defined as positional, and it supports the builder pattern for adding arguments.  `RequestParser` will take the positional
definitions and transform them to act like optional arguments (optional arguments in `argparse` can still have `required=True`).

```python
from typing import List

from flask import Flask

from lc_flask_reqparser import RequestParser


app = Flask(__name__)


def CommaSeparatedList(arg: str) -> List[str]:
    """Convert string representation of CSV to list of str."""
    return arg.split(",")


@app.route("/api/describe/person")
def describe_person():
    """API endpoint to describe information about a person."""
    parser = (RequestParser()
              .add_argument("name", required=True)
              .add_argument("nicknames", type=CommaSeparatedList))
    args, _ = parser.parse_args()
    // use args.name or args.nicknames list to lookup user in database
    // and return information in JSON form.
```

Note that `RequestParser.parse_args` returns a tuple containing the `Namespace` with defined arguments, as well as
a list of the remaining (undefined) arguments.  If an API endpoint only cares about defined arguments, it can safely
ignore the second element of the tuple like the example above.

## Contributing/Suggestions

Contributions and suggestions are welcome! To make a feature request, report a bug, or otherwise comment on existing
functionality, please file an issue. For contributions please submit a PR, but make sure to lint, type-check, and test
your code before doing so. Thanks in advance!
