"""Output field formats. Banking generation runs before representation conversion."""
from decimal import Decimal, InvalidOperation
import pandas as pd
from banksynth.catalog import BY_ID

TYPES = ('text', 'integer', 'decimal', 'boolean', 'date', 'datetime')


def default_format(field_id):
    f = BY_ID[field_id]
    return {'type': f.dtype, 'length': 0, 'scale': 4 if f.dtype == 'decimal' else 0}


def protected(field_id):
    return BY_ID[field_id].rule == 'id' or BY_ID[field_id].rule.startswith('fk:')


def validate_formats(options, selected):
    if options is None:
        return {}
    if not isinstance(options, dict):
        raise ValueError('Field formats must be an object keyed by field ID.')
    normalized = {}
    for fid, raw in options.items():
        if fid not in BY_ID or fid not in selected:
            raise ValueError(f'Format specified for an unknown or unselected field: {fid}')
        if not isinstance(raw, dict) or set(raw) - {'type', 'length', 'scale'}:
            raise ValueError(f'{fid}: use type, length and scale only.')
        spec = default_format(fid) | raw
        if spec['type'] not in TYPES:
            raise ValueError(f'{fid}: choose a supported output type.')
        for key, maximum in [('length', 512), ('scale', 6)]:
            value = spec[key]
            if type(value) is not int or not 0 <= value <= maximum:
                raise ValueError(f'{fid}: {key} must be a whole number from 0 to {maximum}.')
        if protected(fid) and spec != default_format(fid):
            raise ValueError(f'{fid}: join keys use fixed text type and automatic length (0). Reset this row to its defaults.')
        if spec['type'] in ('boolean', 'date', 'datetime') and spec['length']:
            raise ValueError(f'{fid}: {spec["type"]} has a fixed format; set length to 0.')
        if spec['type'] == 'decimal' and spec['length'] and spec['scale'] >= spec['length']:
            raise ValueError(f'{fid}: numeric length must exceed decimal places.')
        if spec != default_format(fid):
            normalized[fid] = spec
    return normalized


def apply_formats(tables, options, selected):
    options = validate_formats(options, selected)
    checks = []
    for fid, spec in options.items():
        table, col = fid.split('.')
        series = tables[table][col]
        dtype, length, scale = spec['type'], spec['length'], spec['scale']
        original = BY_ID[fid].dtype
        try:
            if dtype == 'text':
                converted = series.astype('string')
                truncated = int((converted.str.len() > length).sum()) if length else 0
                if length:
                    converted = converted.str.slice(0, length)
                detail = f'Text; max {length or "automatic"} characters; {truncated} values shortened'
            elif dtype in ('integer', 'decimal'):
                if original in ('date', 'datetime'):
                    raise ValueError('Dates cannot be converted to numeric values.')
                values = []
                for item in series:
                    number = Decimal(int(item)) if isinstance(item, bool) else Decimal(str(item))
                    if not number.is_finite():
                        raise ValueError('Non-finite numeric value.')
                    if dtype == 'integer':
                        if number != number.to_integral_value():
                            raise ValueError('Fractional values cannot be represented as integers without losing value.')
                        if not -(2**63) <= number <= 2**63 - 1:
                            raise ValueError('Integer is outside the supported 64-bit range.')
                    elif number != number.quantize(Decimal(1).scaleb(-scale)):
                        raise ValueError(f'Values need more than {scale} decimal places. Increase decimal places.')
                    digits = max(1, number.copy_abs().adjusted()+1) + (scale if dtype == 'decimal' else 0)
                    if length and digits > length:
                        raise ValueError(f'Values exceed numeric length {length}. Increase length or use 0 (automatic).')
                    values.append(int(number) if dtype == 'integer' else float(number))
                converted = pd.Series(values, index=series.index, dtype='int64' if dtype == 'integer' else 'float64')
                detail = f'{dtype}; length {length or "automatic"}; decimal places {scale if dtype == "decimal" else 0}; lossless conversion'
            elif dtype == 'boolean':
                mapping = {'true': True, 'false': False, '1': True, '0': False, '1.0': True, '0.0': False}
                tokens = series.astype(str).str.lower()
                if not tokens.isin(mapping).all():
                    raise ValueError('Boolean conversion accepts only true/false or 0/1.')
                converted = tokens.map(mapping).astype(bool)
                detail = 'Boolean; true or false'
            else:
                if original in ('integer', 'decimal', 'boolean'):
                    raise ValueError('Numeric/boolean fields cannot be reinterpreted as dates.')
                parsed = pd.to_datetime(series, errors='raise', format='ISO8601')
                if dtype == 'date' and not (parsed == parsed.dt.normalize()).all():
                    raise ValueError('Date conversion would discard the time. Choose datetime or text.')
                converted = parsed.dt.strftime('%Y-%m-%d' if dtype == 'date' else '%Y-%m-%dT%H:%M:%S').astype('string')
                detail = 'ISO date' if dtype == 'date' else 'ISO datetime'
            tables[table][col] = converted
        except (ValueError, TypeError, InvalidOperation, OverflowError) as exc:
            raise ValueError(f'{fid}: {exc}') from exc
        checks.append({'check': f'{fid}: output format', 'passed': True, 'detail': detail})
    return checks
