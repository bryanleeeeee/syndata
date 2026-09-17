"""Field selection UI: live suggestions, checkbox grid and output schema edits."""
import hashlib
import json
import pandas as pd
import streamlit as st
from banksynth.catalog import FIELDS, BY_ID, DEFAULT_FIELDS, LABELS, catalog_records, resolve_fields
from banksynth.search import search_fields
from banksynth.schema import TYPES, validate_formats
from banksynth.selection import grid_rows, merge_grid_edits


def invalidate_grid():
    st.session_state.catalog_revision = st.session_state.get('catalog_revision', 0) + 1


def replace_selection(ids):
    st.session_state.chosen_fields = list(ids)
    invalidate_grid()


def add_fields(ids):
    selected = set(st.session_state.chosen_fields) | set(ids)
    replace_selection([f.id for f in FIELDS if f.id in selected])


def sync_dropdown(visible):
    selected = (set(st.session_state.chosen_fields) - set(visible)) | set(st.session_state.field_picker)
    replace_selection([f.id for f in FIELDS if f.id in selected])


def sync_grid(key):
    snapshot = st.session_state.catalog_snapshot
    edits = st.session_state[key].get('edited_rows', {})
    chosen, formats = merge_grid_edits(snapshot['rows'], edits, st.session_state.chosen_fields, st.session_state.field_options)
    st.session_state.chosen_fields = chosen
    st.session_state.field_options = formats


def reset_formats():
    st.session_state.field_options = {}
    invalidate_grid()


def selected_options():
    return {k: v for k, v in st.session_state.get('field_options', {}).items() if k in st.session_state.chosen_fields}


def render_field_picker(on_continue):
    st.session_state.setdefault('chosen_fields', list(DEFAULT_FIELDS))
    st.session_state.setdefault('field_options', {})
    st.session_state.setdefault('catalog_revision', 0)
    a, b, c = st.columns([2.2, 1.2, 1])
    with a:
        query = st.text_input('Search the catalog', placeholder='Type a field, even with a typo: credti scor...', key='field_search', live='350ms', icon=':material/search:', max_chars=120)
    with b:
        domain = st.selectbox('Banking domain', ['All domains'] + list(LABELS), format_func=lambda x: 'All domains' if x == 'All domains' else LABELS[x], key='catalog_domain')
    with c:
        dtype = st.selectbox('Data type', ['All types'] + list(TYPES))
    candidates = [f for f in FIELDS if (domain == 'All domains' or f.table == domain) and (dtype == 'All types' or f.dtype == dtype)]
    matches = search_fields(query, candidates)
    if query:
        st.caption('Suggested matches / click to add. Suggestions update as you type and respect the filters above.')
        with st.container(horizontal=True):
            for f in matches[:6]:
                already = f.id in st.session_state.chosen_fields
                st.button(f'{f.label} / {LABELS[f.table]}', key=f'suggest_{f.id}', icon=':material/check:' if already else ':material/add:', disabled=already, on_click=add_fields, args=([f.id],))
    with st.container(horizontal=True, vertical_alignment='center'):
        only_selected = st.toggle('Selected only', key='only_selected')
        st.button('Select all 500', on_click=replace_selection, args=([f.id for f in FIELDS],))
        st.button('Clear', on_click=replace_selection, args=([],))
        st.button('Restore starter fields', on_click=replace_selection, args=(DEFAULT_FIELDS,), type='tertiary')
    visible = [f for f in matches if not only_selected or f.id in st.session_state.chosen_fields]
    ids = [f.id for f in visible]
    # Explicit canonical state makes all entry methods agree on the next rerun.
    st.session_state.field_picker = [x for x in st.session_state.chosen_fields if x in ids]
    st.multiselect('Select one or multiple fields', ids, key='field_picker', format_func=lambda x: f'{BY_ID[x].label} / {LABELS[BY_ID[x].table]}', on_change=sync_dropdown, args=(ids,), placeholder='Or select from the searchable dropdown...', wrap=False, filter_mode='fuzzy')
    with st.container(horizontal=True, vertical_alignment='center'):
        st.button(f'Add all {len(ids)} matches', on_click=add_fields, args=(ids,), disabled=not ids, icon=':material/playlist_add:')
        st.caption(f'{len(ids)} fields shown. Tick Include to select; double-click Type, Length or Decimals to edit.')
    if not visible:
        st.info('No fields match. Try a shorter search or choose All domains / All types.')
    else:
        signature = hashlib.sha256(json.dumps([ids, st.session_state.catalog_revision]).encode()).hexdigest()[:16]
        key = f'catalog_editor_{signature}'
        if st.session_state.get('catalog_snapshot', {}).get('key') != key:
            st.session_state.catalog_snapshot = {'key': key, 'rows': grid_rows(visible, st.session_state.chosen_fields, st.session_state.field_options)}
        snapshot = st.session_state.catalog_snapshot
        # Keep a fixed baseline while this grid is active. The callback merges only
        # user edits into canonical state, avoiding the data_editor double-edit bug.
        st.data_editor(pd.DataFrame(snapshot['rows']), hide_index=True, height=410,
            column_order=['Include', 'Field', 'Domain', 'Type', 'Length', 'Decimals'],
            disabled=['Field', 'Domain', 'Field ID'], key=key, on_change=sync_grid, args=(key,),
            column_config={
                'Include': st.column_config.CheckboxColumn('Include', width=70, required=True, pinned=True),
                'Field': st.column_config.TextColumn('Field', width=200, pinned=True),
                'Domain': st.column_config.TextColumn('Domain', width=160),
                'Type': st.column_config.SelectboxColumn('Type', options=list(TYPES), required=True, width=115),
                'Length': st.column_config.NumberColumn('Length', min_value=0, max_value=512, step=1, required=True, width=90, help='0 = automatic. Text: maximum characters. Integer: digits excluding sign. Decimal: total digits including decimal places.'),
                'Decimals': st.column_config.NumberColumn('Decimals', min_value=0, max_value=6, step=1, required=True, width=90, help='Used only for decimal output. Conversions that lose numeric value are rejected.'),
            })
    st.caption('Length 0 = automatic. Text is shortened to its maximum length; numeric values must fit without rounding or overflow. Dates and booleans use fixed formats. Primary and foreign keys keep their original text format.')
    selected = st.session_state.chosen_fields
    resolved = resolve_fields(selected) if selected else ()
    added = [x for x in resolved if x not in selected]
    error = None
    try:
        validate_formats(selected_options(), selected)
    except ValueError as exc:
        error = str(exc)
        st.error(error)
    left, right = st.columns([2, 1], gap='large')
    with left:
        with st.container(border=True):
            st.markdown(f'**{len(selected)} selected fields** / {len({BY_ID[x].table for x in resolved})} tables / {len(added)} supporting join keys')
            st.caption(f'{len(selected_options())} customized field formats. Selection and formats are preserved when you search, filter or move between pages.')
            with st.container(horizontal=True):
                st.download_button('Save selection & formats', json.dumps({'selected_fields': selected, 'field_options': selected_options()}, indent=2), 'field-schema.json', 'application/json', icon=':material/download:')
                st.button('Reset field formats', on_click=reset_formats, icon=':material/restart_alt:')
    with right:
        st.button('Continue to generation', type='primary', icon=':material/arrow_forward:', width='stretch', disabled=not selected or bool(error), on_click=on_continue)
    with st.expander(f'Automatically included keys ({len(added)})'):
        st.caption('Only these supporting join fields are added. Other unselected values are excluded from the export.')
        if added:
            st.code('\n'.join(added), language=None)
    with st.expander('Field definitions & schema import', icon=':material/library_books:'):
        detail_options = ids or [f.id for f in FIELDS]
        detail = st.selectbox('Inspect a field', detail_options, format_func=lambda x: f'{x} / {BY_ID[x].label}')
        st.write(BY_ID[detail].description)
        st.caption(f'Original type: {BY_ID[detail].dtype}. Output conversions do not change the underlying banking model.')
        st.download_button('Download all 500 field definitions', pd.DataFrame(catalog_records()).to_csv(index=False), 'forma-field-catalog.csv', 'text/csv')
        pasted = st.text_area('Paste field IDs or saved schema JSON', placeholder='customers.age\naccounts.closing_balance')
        if st.button('Import field list'):
            try:
                payload = json.loads(pasted) if pasted.lstrip().startswith(('[', '{')) else [x.strip() for x in pasted.replace(',', '\n').splitlines() if x.strip()]
                options = payload.get('field_options', {}) if isinstance(payload, dict) else {}
                values = payload.get('selected_fields') if isinstance(payload, dict) else payload
                if not isinstance(values, list) or not all(isinstance(x, str) for x in values):
                    raise ValueError('Provide field IDs or a saved schema with selected_fields and field_options.')
                imported = list(dict.fromkeys(values))
                resolve_fields(imported)
                options = validate_formats(options, imported)
                st.session_state.field_options = options
                replace_selection(imported)
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
