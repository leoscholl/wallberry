import os
import tempfile

import pytest

from wallberry import create_app
from wallberry.db import get_db, init_db


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({
        'TESTING': True,
        'DATABASE': db_path,
    })

    with app.app_context():
        init_db()

    yield app

    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

def test_forecast(client):
    """Test that forecast works."""
    
    rv = client.get('/forecast/currently')
    assert b'Currently' in rv.data
    
    rv = client.get('/forecast/hourly')
    assert b'<div class="row hourly">' in rv.data

    rv = client.get('/forecast/daily')
    assert b'<div class="row daily">' in rv.data

def test_empty_db(client):
    """Start with a blank database."""

    rv = client.get('/log/temperature')
    assert b'Sensor' not in rv.data

    rv = client.get('/thermostat')
    assert b'72' not in rv.data

def test_sensors(client):
    """Test that sensor logging works."""

    rv = client.post('/log', data=dict(
        name='Sensor',
        temperature=72,
        humidity=50,
        pressure=1,
    ), follow_redirects=False)
    assert b'ok' in rv.data
    rv = client.get('/log/temperature')
    assert b'<dt class="col-8">Sensor:</dt>' in rv.data
    assert b'<dd class="col-4">72' in rv.data

def test_thermostat(client):
    """Check thermostat page updates database correctly."""
    
    rv = client.post('/thermostat', data=dict(
        status=1,
        settemp=42,
    ), follow_redirects=True)
    assert b'<h1 class="current-temperature">42' in rv.data

def test_graphs(client):
    """Test that images appear."""

    rv = client.get('/forecast/graph?width=100')
    assert rv.status_code == 200

    rv = client.post('/log', data=dict(
        name='Sensor',
        temperature=72,
        humidity=50,
        pressure=1,
    ), follow_redirects=False)
    assert b'ok' in rv.data
    rv = client.get('/log/graph?width=100')
    assert rv.status_code == 200


