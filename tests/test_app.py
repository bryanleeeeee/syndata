from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")

def button(at, label):
    return next(b for b in at.button if b.label == label)


def test_generate_explore_quality_history_export():
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    assert len(at.session_state["chosen_fields"]) == 12
    button(at, "Continue to generation").click().run()
    at.number_input(key="customers").set_value(30)
    at.number_input(key="tx_count").set_value(3)
    button(at, "Generate selected fields").click().run()
    assert not at.exception
    assert len(at.session_state["result"]["tables"]["customers"]) == 30
    at.button(key="prepare_export").click().run()
    assert at.session_state["archive"].startswith(b"PK")
    at.switch_page("app_pages/explorer.py").run()
    assert not at.exception
    at.text_input[0].set_value("SYN-C0000001").run()
    assert len(at.dataframe[0].value) == 1
    at.switch_page("app_pages/quality.py").run()
    assert not at.exception
    at.switch_page("app_pages/history.py").run()
    assert not at.exception
    button(at, "Replay this configuration").click().run()
    assert len(at.session_state["history"]) == 2
    at.switch_page("app_pages/deploy.py").run()
    assert not at.exception


def test_invalid_size_keeps_previous_result():
    at = AppTest.from_file(APP, default_timeout=30).run()
    at.switch_page("app_pages/explorer.py").run()
    previous = at.session_state["result"]["id"]
    at.switch_page("app_pages/studio.py").run()
    button(at, "Continue to generation").click().run()
    at.number_input(key="customers").set_value(10000)
    at.number_input(key="tx_count").set_value(100)
    button(at, "Generate selected fields").click().run()
    assert at.error
    assert at.session_state["result"]["id"] == previous
    assert not at.exception


def test_single_field_search_filter_and_persistence():
    at = AppTest.from_file(APP, default_timeout=30).run()
    button(at, "Clear").click().run()
    assert not at.session_state["chosen_fields"]
    assert button(at, "Continue to generation").disabled
    at.text_input(key="field_search").set_value("credit_score").run()
    at.multiselect(key="field_picker").set_value(["customers.credit_score"]).run()
    assert at.session_state["chosen_fields"] == ["customers.credit_score"]
    at.text_input(key="field_search").set_value("does-not-exist").run()
    assert at.session_state["chosen_fields"] == ["customers.credit_score"]
    assert any("No fields match" in x.value for x in at.info)
    at.switch_page("app_pages/quality.py").run()
    at.switch_page("app_pages/studio.py").run()
    assert at.session_state["chosen_fields"] == ["customers.credit_score"]
    button(at, "Continue to generation").click().run()
    at.number_input(key="customers").set_value(10)
    button(at, "Generate selected fields").click().run()
    assert not at.exception
    assert set(at.session_state["result"]["tables"]["customers"]) == {"customer_id", "credit_score"}


def test_select_all_and_domain_add():
    at = AppTest.from_file(APP, default_timeout=30).run()
    button(at, "Select all 500").click().run()
    assert len(at.session_state["chosen_fields"]) == 500
    button(at, "Clear").click().run()
    at.selectbox(key="catalog_domain").set_value("cards").run()
    button(at, "Add all 25 matches").click().run()
    assert len(at.session_state["chosen_fields"]) == 25
    assert all(x.startswith("cards.") for x in at.session_state["chosen_fields"])
    button(at, "Continue to generation").click().run()
    at.number_input(key="customers").set_value(10)
    button(at, "Generate selected fields").click().run()
    assert not at.exception
    assert len(at.session_state["result"]["tables"]["cards"].columns) == 25
    at.switch_page("app_pages/explorer.py").run()
    assert not at.exception


def test_reference_table_only_explorer():
    at = AppTest.from_file(APP, default_timeout=30).run()
    button(at, "Clear").click().run()
    at.multiselect(key="field_picker").set_value(["branches.branch_name"]).run()
    button(at, "Continue to generation").click().run()
    button(at, "Generate selected fields").click().run()
    at.switch_page("app_pages/explorer.py").run()
    assert not at.exception
    assert set(at.session_state["result"]["tables"]) == {"branches"}
