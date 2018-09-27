import json
import sys

from os import listdir, remove
from os.path import exists
from time import sleep

from apiHandler import status_transfer, status_ingest, start_transfer
from constants import AppConstants
from dbHandler import db_handler
from logger import write_log

AppConstants = AppConstants()


def get_all_source_folder():
    source_list = {str(AppConstants.EBOOK): listdir(str(AppConstants.EBOOK_SOURCE_PATH)),
                   str(AppConstants.RETRO): listdir(str(AppConstants.RETRO_SOURCE_PATH)),
                   str(AppConstants.FREIDOK): listdir(str(AppConstants.FREIDOK_SOURCE_PATH))}
    return source_list


def get_all_transfers_ingests_db():
    t_list = db_handler(AppConstants.TRANSFER, AppConstants.GET_ALL)
    return t_list


def insert_sources_db(source_list):
    for item in source_list:
        db_handler(AppConstants.SOURCE, AppConstants.INSERT, item)
    return


def insert_transfer_db(s_id, s_name, acnumber, uuid, status, conf):
    return db_handler(AppConstants.TRANSFER, AppConstants.INSERT, s_id, s_name, acnumber, uuid, status, conf)


def restart_transfer_api_db():
    start_transfer()
    db_handler(AppConstants.TRANSFER, AppConstants.UPDATE_STATUS_TRANSFER)
    pass


# def check_transfer_api(uuid):
#    status = status_transfer(uuid) and status_ingest(uuid)
#    if status == AppConstants.FAILED:
#        restart_transfer_api_db()
#    pass


# TODO: When db_list has entries, check for updates from API. Ignore all finished Ingests in db_list.
# TODO: Implement delete routine for new finished items from DB after check with API
def refresh_transfer_list_db():
    db_list = get_transfer_db()
    if len(db_list) > 0:
        for item in db_list:
            transfer_item = get_transfer_api(item[5])
            db_handler(AppConstants.TRANSFER, AppConstants.UPDATE_STATUS_TRANSFER, transfer_item["status"], item[5])
    # TODO: wenn Failed restart anstoßen und
    # TODO: status transfer überprüfen ob sip_uuid vorhanden ist. wenn nicht, status überprüfen.
    else:

        print("No Transfer in DB.")
    return


def check_delete_dates():
    pass


def clean_db():
    write_log("Cleaned DB", "[INFO]")
    pass


def get_sources_from_db():
    return db_handler(AppConstants.SOURCE, AppConstants.GET_ALL)


def get_unstarted_source_from_db():
    return db_handler(AppConstants.SOURCE, AppConstants.GET_UNSTARTED)


def compare_source_db(list_source, list_db):
    list_new_source = {}
    for key, value in list_source.items():
        if value not in list_db:
            list_new_source[key] = value
    refresh_source_db(list_new_source)
    pass


def refresh_source_db(list_new_source):
    for key in list_new_source:
        for value in list_new_source[key]:
            success = db_handler(AppConstants.SOURCE, AppConstants.INSERT, value, key)
            if success:
                write_log("Insert in DB from " + str(key) + "/" + str(value) + " was successful", "[INFO]")
            else:
                write_log(str(key) + "/" + str(value) + " already exist in DB", "[ERROR]")
    return


def get_transfer_db():
    return db_handler(AppConstants.TRANSFER, AppConstants.GET_ALL)


def get_active_transfers_db():
    refresh_transfer_list_db()
    return db_handler(AppConstants.TRANSFER, AppConstants.GET_ACTIVE)


# Returns JSON Body of an UUID from transfer or ingest tab, when available
def get_transfer_api(uuid):
    t_status = json.loads(status_transfer(uuid).text)
    if "sip_uuid" in t_status:
        if db_handler(AppConstants.TRANSFER, AppConstants.UPDATE_SIP_UUID_TRANSFER, uuid, t_status["sip_uuid"]):
            return json.loads(status_ingest(t_status["sip_uuid"]).text)
    else:
        return t_status


def update_source(id):
    return db_handler(AppConstants.SOURCE, AppConstants.UPDATE_STATUS_SOURCE, id)


def start_transfer_auto():
    if len(get_active_transfers_db()) < 2:
        new_ingest = get_unstarted_source_from_db()
        r = start_transfer(new_ingest[1], new_ingest[2], new_ingest[0],
                           (str(AppConstants.SOURCE_DICT[new_ingest[2]]) + "/" + new_ingest[1]),
                           AppConstants.PROCESS_AUTOMATED)
        if r is not None:
            if r["status"] == 200:
                if update_source(new_ingest[0]):
                    write_log("Update source was successful - " + str(new_ingest), "[INFO]")
                if insert_transfer_db(new_ingest[0], new_ingest[1], new_ingest[0], r["uuid"], AppConstants.PROCESSING,
                                      AppConstants.PROCESS_AUTOMATED):
                    write_log("Update transfer in DB was successful - " + str(new_ingest), "[INFO]")
            else:
                write_log("Status Code: " + str(r["status"]) + " " + str(r.values()), "[ERROR]")
    else:
        sleep(5)
    pass


def init():
    if sys.argv[-1] == "DEBUG":
        f = open("DEBUG", "w+")
        f.close()
    else:
        if exists(str(AppConstants.DEBUG_PATH)):
            remove(str(AppConstants.DEBUG_PATH))
    list_db = get_sources_from_db()
    list_source = get_all_source_folder()
    compare_source_db(list_source, list_db)
    refresh_transfer_list_db()
    return


if __name__ == "__main__":
    init()
    while True:
        start_transfer_auto()
        init()
    pass
