matrix-floppy 💾
===============

Save your Matrix history.

[![PyPI](https://img.shields.io/pypi/v/matrix-floppy)](https://pypi.org/project/matrix-floppy/)
[![License](https://img.shields.io/badge/License-BSD%202--Clause-orange.svg)](https://opensource.org/licenses/BSD-2-Clause)

Motivation
----------

My motivation for writing this application is to give me an offline browseable
and searchable archive of my Matrix chat history. This can be handy if my
homeserver is down, or if I want to move homeserver, or just to be able to
search encrypted chat history without needing to use Element Desktop.

Features
--------

Media types:

* [x] Unencrypted messages
* [x] Encrypted messages
* [ ] Images
* [ ] Videos
* [ ] Reactions

Operation modes:

* [x] Batch
* [ ] Real-time client

Output formats:

* [x] HTML
* [ ] Plain-text
* [ ] JSON

Installation
------------

Use `python3 setup.py install` to install this package. You can do this
system-wide or inside a virtualenv at your preference.

For development, dependencies are managed using the `Pipfile` although a
`requirements.txt` file is also provided, generated via a make target.

License
-------

Copyright (C) Iain R. Learmonth 2021. See `COPYING` for permissions.
