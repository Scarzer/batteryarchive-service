from app.model import ArchiveOperator
from app.aio import ArchiveExporter
from app.archive_cell import ArchiveCell
from flask import request, jsonify
import pandas as pd
from app.archive_constants import (LABEL, SLASH,
                                   CELL_LIST_FILE_NAME, TEST_TYPE, FORMAT)
import uuid
import threading
# Routes
"tracker -> msg"
global status
status = {}
"tracker -> id"
global source
source = {}

def root():
    return jsonify('Hello Battery Archive!')


def liveness():
    return "Alive", 200


def readiness():
    return "Ready", 200


def finish(tracker):
    if tracker in status:
        status[tracker] = "FINISHED"
        return {"tracker": tracker, "dataset_id": source[tracker]}, 200
    return {"tracker": "not found", "dataset_id": source[tracker]}, 200

def get_cells():
    """get_cell
    Gets all cells
    :rtype: list of Cell
    """

    ao = ArchiveOperator()
    archive_cells = ao.get_all_cell_meta()
    result = [cell.to_dict() for cell in archive_cells]
    return jsonify(result)


def get_cell_with_id(cell_id):
    ao = ArchiveOperator()
    archive_cells = ao.get_all_cell_meta_with_id(cell_id)
    result = [cell.to_dict() for cell in archive_cells]
    return jsonify(result)


def get_test(test_name):
    """
    """
    ao = ArchiveOperator()
    if test_name == TEST_TYPE.CYCLE.value:
        archive_cells = ao.get_all_cycle_meta()
        result = [cell.to_dict() for cell in archive_cells]
        return jsonify(result)
    if test_name == TEST_TYPE.ABUSE.value:
        archive_cells = ao.get_all_abuse_meta()
        result = [cell.to_dict() for cell in archive_cells]
        return jsonify(result)


def get_ts(test_name):
    if test_name == TEST_TYPE.CYCLE.value:
        archive_cells = ArchiveOperator().get_all_cycle_ts()
        result = [cell.to_dict() for cell in archive_cells]
        return jsonify(result)
    if test_name == TEST_TYPE.ABUSE.value:
        archive_cells = ArchiveOperator().get_all_abuse_ts()
        result = [cell.to_dict() for cell in archive_cells]
        return jsonify(result)

def get_stats(test_name):
    if test_name == TEST_TYPE.CYCLE.value:
        archive_cells = ArchiveOperator().get_all_cycle_stats()
        result = [cell.to_dict() for cell in archive_cells]
        return jsonify(result)
    if test_name == TEST_TYPE.ABUSE.value:
        return jsonify([])
        # archive_cells = ArchiveOperator().get_all_abuse_ts()
        # result = [cell.to_dict() for cell in archive_cells]
        # return jsonify(result)

def get_test_ts_with_id(cell_id, test_name):
    if test_name == TEST_TYPE.CYCLE.value:
        archive_cells = ArchiveOperator().get_all_cycle_ts_with_id(cell_id)
        result = [cell.to_dict() for cell in archive_cells]
        return jsonify(result)
    if test_name == TEST_TYPE.ABUSE.value:
        archive_cells = ArchiveOperator().get_all_abuse_ts_with_id(cell_id)
        result = [cell.to_dict() for cell in archive_cells]
        return jsonify(result)

def get_stats_with_id(cell_id, test_name):
    if test_name == TEST_TYPE.CYCLE.value:
        archive_cells = ArchiveOperator().get_all_cycle_stats_with_id(cell_id)
        result = [cell.to_dict() for cell in archive_cells]
        return jsonify(result)
    if test_name == TEST_TYPE.ABUSE.value:
        return jsonify([])

def get_meta_with_id(cell_id, test_name):
    if test_name == TEST_TYPE.CYCLE.value:
        archive_cells = ArchiveOperator().get_all_cycle_meta_with_id(cell_id)
        result = [cell.to_dict() for cell in archive_cells]
        return jsonify(result)
    if test_name == TEST_TYPE.ABUSE.value:
        archive_cells = ArchiveOperator().get_all_abuse_meta_with_id(cell_id)
        result = [cell.to_dict() for cell in archive_cells]
        return jsonify(result)


def add_cell():
    body = request.json
    path = body.get('path')
    print(path)
    if import_cells_xls_to_db(path):
        return "Upload Successful", 200
    return "Upload Failed", 200


# EXPORTERS


def export_cycle_cells_to_fmt(cell_list_path,
                              output_path: str,
                              fmt: str = "csv"):
    # TODO: This implies cell_list must be xlsx, this can be written in CSV
    df_excel = pd.read_excel(cell_list_path + CELL_LIST_FILE_NAME)
    # TODO: Refactor this to a join instead of looping slowly
    for i in df_excel.index:
        cell_id = df_excel[LABEL.CELL_ID.value][i]
        df = ArchiveOperator().get_df_cell_meta_with_id(cell_id)
        if not df.empty:
            if fmt == FORMAT.CSV.value:
                export_cycle_meta_data_with_id_to_fmt(cell_id, output_path,
                                                      FORMAT.CSV.value)
                export_cycle_ts_data_csv(cell_id, output_path)
            if fmt == FORMAT.FEATHER.value:
                export_cycle_meta_data_with_id_to_fmt(cell_id, output_path,
                                                      FORMAT.FEATHER.value)
                export_cycle_ts_data_feather(cell_id, output_path)


"""
generate_cycle_data queries data from the database and exports to csv

:param cell_id: Absolute Path to the cell_list directory
:param path: Path to the cell_list directory
:return: Boolean True if method succeeds False if method fails
"""


def export_cycle_meta_data_with_id_to_fmt(cell_id: str,
                                          out_path: str,
                                          fmt: str = "csv"):
    if fmt == FORMAT.CSV.value:
        return ArchiveExporter.write_to_csv(
            ArchiveOperator().get_df_cycle_meta_with_id(cell_id), cell_id,
            out_path, "cycle_data")
    if fmt == FORMAT.FEATHER.value:
        return ArchiveExporter.write_to_feather(
            ArchiveOperator().get_df_cycle_meta_with_id(cell_id), cell_id,
            out_path, "cycle_data")


"""
generate_timeseries_data queries data from the database and exports to csv

:param session: Database session that 
:param cell_id: Absolute Path to the cell_list directory
:param path: Path to the cell_list directory
:return: Boolean True if successful False if method fails
"""


def export_cycle_ts_data_csv(cell_id: str, path: str):
    return ArchiveExporter.write_to_csv(
        ArchiveOperator().get_df_cycle_ts_with_cell_id(cell_id), cell_id, path,
        "timeseries_data")


def export_cycle_ts_data_feather(cell_id: str, path: str):
    return ArchiveExporter.write_to_feather(
        ArchiveOperator().get_df_cycle_ts_with_cell_id(cell_id), cell_id, path,
        "timeseries_data")


# Importers


# def import_cells_xls_to_db(cell_list_path):
#     df = pd.read_excel(cell_list_path + CELL_LIST_FILE_NAME)
#     cells = []
#     for i in df.index:
#         cell = ArchiveCell(cell_id=df[LABEL.CELL_ID.value][i],
#                            test_type=str(df[LABEL.TEST.value][i]),
#                            file_id=df[LABEL.FILE_ID.value][i],
#                            file_type=str(df[LABEL.FILE_TYPE.value][i]),
#                            tester=df[LABEL.TESTER.value][i],
#                            file_path=cell_list_path +
#                            df[LABEL.FILE_ID.value][i] + SLASH,
#                            metadata=df.iloc[i])
#         cells.append(cell)
#     return ArchiveOperator().add_cells_to_db(cells)


def import_cells_xls_to_db(cell_list_path):
    return add_df_to_db(pd.read_excel(cell_list_path + CELL_LIST_FILE_NAME),
                        cell_list_path)


def import_cells_feather_to_db(cell_list_path):
    return add_df_to_db(pd.read_feather(cell_list_path + CELL_LIST_FILE_NAME),
                        cell_list_path)


def add_df_to_db(df, cell_list_path):
    cells = []
    for i in df.index:
        cell = ArchiveCell(cell_id=df[LABEL.CELL_ID.value][i],
                           test_type=str(df[LABEL.TEST.value][i]),
                           file_id=df[LABEL.FILE_ID.value][i],
                           file_type=str(df[LABEL.FILE_TYPE.value][i]),
                           tester=df[LABEL.TESTER.value][i],
                           file_path=cell_list_path +
                           df[LABEL.FILE_ID.value][i] + SLASH,
                           metadata=df.iloc[i])
        cells.append(cell)
    return ArchiveOperator().add_cells_to_db(cells)


def update_cycle_cells(cell_list_path):
    df_excel = pd.read_excel(cell_list_path + CELL_LIST_FILE_NAME)
    ao = ArchiveOperator()
    for i in df_excel.index:
        cell_id = df_excel[LABEL.CELL_ID.value][i]
        df = ArchiveOperator().get_df_cell_meta_with_id(cell_id)
        if df.empty:
            print("cell:" + cell_id + " not found")
            continue
        ao.remove_cell_from_archive(cell_id)
    import_cells_xls_to_db(cell_list_path)
    return True
