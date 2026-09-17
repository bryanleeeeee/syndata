"""Pure helpers for editable field selection and schema state."""
from banksynth.catalog import FIELDS, BY_ID, LABELS
from banksynth.schema import default_format


def grid_rows(fields, selected, formats):
    return [{'Include': f.id in selected, 'Field': f.label, 'Domain': LABELS[f.table],
             'Type': (default_format(f.id) | formats.get(f.id, {}))['type'],
             'Length': (default_format(f.id) | formats.get(f.id, {}))['length'],
             'Decimals': (default_format(f.id) | formats.get(f.id, {}))['scale'],
             'Field ID': f.id} for f in fields]


def merge_grid_edits(rows, edits, selected, formats):
    selected = set(selected)
    formats = dict(formats)
    for index, changes in edits.items():
        index = int(index)
        if not 0 <= index < len(rows):
            raise ValueError('Invalid catalog row.')
        row = rows[index] | changes
        fid = rows[index]['Field ID']
        if row['Include']:
            selected.add(fid)
        else:
            selected.discard(fid)
        spec = {'type': row['Type'], 'length': row['Length'], 'scale': row['Decimals']}
        if spec == default_format(fid):
            formats.pop(fid, None)
        else:
            formats[fid] = spec
    return [f.id for f in FIELDS if f.id in selected], formats
