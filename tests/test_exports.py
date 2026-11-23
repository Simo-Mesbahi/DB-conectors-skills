import csv
import json

import pandas as pd
import pytest

from data_processing.export_results import (
    export_to_csv,
    export_to_excel,
    export_to_json,
)


def test_csv_neutralizes_formula_strings_and_headers_without_changing_input(tmp_path):
    frame = pd.DataFrame(
        {"=heading": ["=1+1", "+SUM(A1)", "  @command", "\t=run", "normal", -3]}
    )
    original = frame.copy(deep=True)
    target = tmp_path / "data.csv"
    export_to_csv(frame, target)
    rows = list(csv.reader(target.open()))
    assert rows[0] == ["'=heading"]
    assert [row[0] for row in rows[1:]] == [
        "'=1+1",
        "'+SUM(A1)",
        "'  @command",
        "'\t=run",
        "normal",
        "-3",
    ]
    pd.testing.assert_frame_equal(frame, original)


def test_trusted_csv_can_explicitly_preserve_raw_strings(tmp_path):
    target = tmp_path / "data.csv"
    export_to_csv(pd.DataFrame({"text": ["=1+1"]}), target, safe_cells=False)
    assert list(csv.reader(target.open()))[1] == ["=1+1"]


def test_csv_failure_preserves_old_target_and_cleans_temporary_file(
    tmp_path, monkeypatch
):
    target = tmp_path / "report.csv"
    target.write_text("previous report")

    def fail(self, path, **kwargs):
        path.write_text("partial")
        raise OSError("serialization interrupted")

    monkeypatch.setattr(pd.DataFrame, "to_csv", fail)
    with pytest.raises(OSError):
        export_to_csv(pd.DataFrame({"x": [1]}), target)
    assert target.read_text() == "previous report"
    assert list(tmp_path.iterdir()) == [target]


def test_json_preserves_literal_strings_and_replaces_complete_output(tmp_path):
    target = tmp_path / "nested" / "report.json"
    export_to_json(pd.DataFrame({"text": ["=1+1"], "value": [-2]}), target)
    assert json.loads(target.read_text()) == [{"text": "=1+1", "value": -2}]


def test_json_failure_does_not_create_a_partial_target(tmp_path, monkeypatch):
    target = tmp_path / "report.json"

    def fail(self, path, **kwargs):
        path.write_text("partial")
        raise RuntimeError("interrupted")

    monkeypatch.setattr(pd.DataFrame, "to_json", fail)
    with pytest.raises(RuntimeError):
        export_to_json(pd.DataFrame({"x": [1]}), target)
    assert list(tmp_path.iterdir()) == []


def test_excel_formula_cells_are_literal_and_numbers_remain_numeric(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    target = tmp_path / "report.xlsx"
    export_to_excel(pd.DataFrame({"=heading": ["=1+1"], "value": [-3]}), target)
    workbook = openpyxl.load_workbook(target, data_only=False)
    try:
        sheet = workbook["Résultats"]
        assert sheet["A1"].value == "'=heading"
        assert sheet["A2"].data_type == "s"
        assert sheet["A2"].value == "'=1+1"
        assert sheet["B2"].value == -3
        assert sheet["B2"].data_type == "n"
    finally:
        workbook.close()


def test_invalid_excel_sheet_preserves_the_previous_workbook(tmp_path):
    pytest.importorskip("openpyxl")
    target = tmp_path / "report.xlsx"
    export_to_excel(pd.DataFrame({"x": [1]}), target)
    old = target.read_bytes()
    with pytest.raises(ValueError):
        export_to_excel(pd.DataFrame({"x": [2]}), target, sheet_name="invalid[]")
    assert target.read_bytes() == old
    assert list(tmp_path.iterdir()) == [target]


@pytest.mark.parametrize("extension", [".zip", ".tar.gz", ".gz"])
def test_compressed_csv_and_json_preserve_format_and_archive_member_names(
    tmp_path, extension
):
    import tarfile
    import zipfile

    frame = pd.DataFrame({"number": [1, -2]})
    csv_path = tmp_path / ("report.csv" + extension)
    json_path = tmp_path / ("report.json" + extension)
    export_to_csv(frame, csv_path)
    export_to_json(frame, json_path)
    pd.testing.assert_frame_equal(pd.read_csv(csv_path), frame)
    pd.testing.assert_frame_equal(pd.read_json(json_path), frame)
    for path, member in ((csv_path, "report.csv"), (json_path, "report.json")):
        if extension == ".zip":
            with zipfile.ZipFile(path) as archive:
                assert archive.namelist() == [member]
        elif extension == ".tar.gz":
            with tarfile.open(path) as archive:
                assert archive.getnames() == [member]
