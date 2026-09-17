from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from banksynth.engine import Config
from banksynth.field_engine import generate_selected
from banksynth.catalog import FIELDS
from banksynth.limits import get_limits


def test_public_budget(monkeypatch):
    monkeypatch.setenv('BANKSYNTH_DEPLOYMENT', 'community')
    assert get_limits()['customers'] == 2000
    with pytest.raises(ValueError, match='customers'):
        Config(customers=3000).validate()
    with pytest.raises(ValueError, match='transactions'):
        Config(customers=2000, transactions_per_account=100).validate()
    with pytest.raises(ValueError, match='working-cell'):
        generate_selected(Config(customers=2000, transactions_per_account=25), [f.id for f in FIELDS])


def test_cloud_entrypoint_generates_without_uploads(monkeypatch):
    monkeypatch.setenv('BANKSYNTH_DEPLOYMENT', 'community')
    entry = str(Path(__file__).resolve().parents[1] / 'streamlit_app.py')
    at = AppTest.from_file(entry, default_timeout=30).run()
    assert not at.exception
    next(b for b in at.button if b.label == 'Continue to generation').click().run()
    assert at.selectbox(key='engine').options == ['Simulator']
    assert len(at.get('file_uploader')) == 0
    at.number_input(key='customers').set_value(10)
    next(b for b in at.button if b.label == 'Generate selected fields').click().run()
    assert not at.exception
    assert len(at.session_state['result']['tables']['customers']) == 10
