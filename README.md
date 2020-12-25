# rsync-python-implementation

> The implementation of rsync algorithm in python with folder monitoring and syncing between a client and a server.

## To run client and server

```
python3 server.py FOLDER_PATH
python3 client.py FOLDER_PATH
```

## To run tests

```
# Install pytest
pip3 install --user pytest

# Create test folders
mkdir -p /tmp/dropbox/server
mkdir -p /tmp/dropbox/client

# Set env variables to run a client and server
export SERVER_CMD='python3 server.py /tmp/dropbox/server'
export CLIENT_CMD='python3 client.py /tmp/dropbox/client'

# Run pytest: Verbose, with stdout, filter by test name
pytest -vv -s . -k 'test_some_name'
# Run pytest: Quiet, show summary in the end
pytest -q -rapP
# Run pytest: Verbose, with stdout, show summary in the end
pytest -s -vv -q -rapP
