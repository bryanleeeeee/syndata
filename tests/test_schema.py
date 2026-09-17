import io
import json
import zipfile
from dataclasses import replace
import pandas as pd
import pytest
from banksynth.catalog import BY_ID
from banksynth.engine import Config
from banksynth.field_engine import generate_selected
from banksynth.schema import validate_formats, default_format
from banksynth.search import search_fields
from banksynth.selection import grid_rows, merge_grid_edits
from banksynth.export import bundle


def test_fuzzy_typo_and_exact_order():
    assert search_fields('credti scor')[0].id == 'customers.credit_score'
    assert search_fields('customers.age')[0].id == 'customers.age'
    assert not search_fields('zzzxxyyqq123')
    assert search_fields('emal', [BY_ID['customers.email']])[0].id == 'customers.email'


def test_checkbox_and_format_edits_keep_hidden_selection():
    rows = grid_rows([BY_ID['customers.age'], BY_ID['customers.display_name']], [], {})
    selected, options = merge_grid_edits(rows, {0: {'Include': True, 'Type': 'text', 'Length': 4}}, ['cards.credit_limit'], {})
    assert selected == ['customers.age', 'cards.credit_limit']
    assert options['customers.age']['type'] == 'text'
    selected, options = merge_grid_edits(rows, {0: {'Include': False, 'Type': 'text', 'Length': 4}, 1: {'Include': True}}, selected, options)
    assert selected == ['customers.display_name', 'cards.credit_limit']
    assert options['customers.age']['length'] == 4


def test_generated_lengths_types_and_manifest():
    chosen = ('customers.display_name', 'customers.age', 'customers.credit_score')
    options = {'customers.display_name': {'type': 'text', 'length': 12},
               'customers.age': {'type': 'text', 'length': 2},
               'customers.credit_score': {'type': 'decimal', 'length': 5, 'scale': 2}}
    cfg = Config(customers=20, selected_fields=chosen, field_options=options)
    tables, checks = generate_selected(cfg, chosen)
    c = tables['customers']
    assert c.display_name.str.len().max() == 12
    assert c.age.str.len().max() <= 2
    assert pd.api.types.is_float_dtype(c.credit_score)
    assert all(x['passed'] for x in checks)
    with zipfile.ZipFile(io.BytesIO(bundle(tables, cfg, checks))) as z:
        manifest = json.loads(z.read('manifest.json'))
        assert manifest['config']['field_options'] == options
        definitions = json.loads(z.read('field_definitions.json'))
        f = next(x for x in definitions if x['field_id'] == 'customers.display_name')
        assert f['length'] == 12 and f['type'] == 'text'
        assert pd.read_csv(z.open('customers.csv')).display_name.str.len().max() == 12
    replay, _ = generate_selected(Config(**json.loads(json.dumps(manifest['config']))), chosen)
    pd.testing.assert_frame_equal(c, replay['customers'])


@pytest.mark.parametrize('fid,option', [
    ('customers.age', {'type': 'integer', 'length': 1}),
    ('customers.annual_income', {'type': 'integer'}),
    ('customers.display_name', {'type': 'integer'}),
    ('customers.age', {'type': 'boolean'}),
    ('customers.age', {'type': 'date'}),
    ('transactions.timestamp', {'type': 'date'}),
    ('customers.annual_income', {'type': 'decimal', 'scale': 0}),
])
def test_invalid_or_lossy_conversion_rejected(fid, option):
    cfg = Config(customers=20, selected_fields=(fid,), field_options={fid: option})
    with pytest.raises(ValueError, match=fid):
        generate_selected(cfg, (fid,))


@pytest.mark.parametrize('fid,option', [
    ('customers.customer_id', {'type': 'integer'}),
    ('accounts.customer_id', {'length': 3}),
    ('customers.age', {'type': 'bad'}),
    ('customers.age', {'length': -1}),
    ('customers.age', {'length': 1.2}),
    ('customers.age', {'length': True}),
    ('customers.age', {'length': 513}),
    ('customers.age', {'type': 'decimal', 'length': 3, 'scale': 4}),
    ('customers.age', {'type': 'boolean', 'length': 1}),
])
def test_invalid_schema_rejected(fid, option):
    with pytest.raises(ValueError):
        validate_formats({fid: option}, [fid])


def test_lossless_conversions_and_no_selected_loans():
    chosen = ('customers.customer_since', 'cards.contactless_enabled', 'loans.principal')
    options = {'customers.customer_since': {'type': 'datetime'}, 'cards.contactless_enabled': {'type': 'integer'}, 'loans.principal': {'type': 'text', 'length': 30}}
    t, checks = generate_selected(Config(customers=10, loan_rate=0, selected_fields=chosen, field_options=options), chosen)
    assert t['customers'].customer_since.str.endswith('T00:00:00').all()
    assert t['cards'].contactless_enabled.isin([0, 1]).all()
    assert t['loans'].empty
    assert all(c['passed'] for c in checks)
