import json

from os import listdir
from time import sleep

from apiHandler import status_transfer, status_ingest, start_transfer
from constants import AppConstants
from dbHandler import db_handler

AppConstants = AppConstants()
transfers = {}


# source_list = {"EBOOK" : [], "RETRO" : [], "FREIDOK" : []}
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


def insert_transfer_db(s_id, s_name, acnumber,  uuid, status, conf):
    return db_handler(AppConstants.TRANSFER, AppConstants.INSERT, s_id, s_name, acnumber,  uuid, status, conf)


def restart_transfer_api_db():
    start_transfer()
    db_handler(AppConstants.TRANSFER, AppConstants.UPDATE_STATUS_TRANSFER)
    pass


#def check_transfer_api(uuid):
#    status = status_transfer(uuid) and status_ingest(uuid)
#    if status == AppConstants.FAILED:
#        restart_transfer_api_db()
#    pass


# TODO: When db_list has entries, check for updates from API. Ignore all finished Ingests in db_list.
# TODO: Implement delete routine for new finished items from DB after check with API
# TODO: Return list of startable source items
def refresh_transfer_list_db():
    db_list = get_transfer_db()
    if len(db_list) > 0:
        # TODO: Check output of db list and look for entries in transfer db
        for item in db_list:
            transfer_item = get_transfer_api(item[4])
            # TODO: mit sip_UUID status abfragen und erneuern in DB
            db_handler(AppConstants.TRANSFER, AppConstants.UPDATE_STATUS_TRANSFER, transfer_item[0], item)
        #TODO: status abfragen
    # TODO: wenn Failed restart anstoßen und
    #TODO: status transfer überprüfen ob sip_uuid vorhanden ist. wenn nicht, status überprüfen.
    else:

        print("No Transfer in DB.")
    return


def check_delete_dates():
    pass


def clean_db():
    write_logs("Cleaned DB", "[INFO]")
    pass


def write_logs(message, log_type):
    print(log_type + " " + message)
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
                write_logs("Insert in DB from " + key + "/" + value + " was successful", "[INFO]")
            else:
                write_logs(key + "/" + value + " already exist in DB", "[ERROR]")
    return


def get_transfer_db():
    return db_handler(AppConstants.TRANSFER, AppConstants.GET_ALL)


def get_active_transfers_db():
    refresh_transfer_list_db()
    return db_handler(AppConstants.TRANSFER, AppConstants.GET_ACTIVE)


# Returns JSON Body of an UUID from transfer or ingest tab, when available
def get_transfer_api(uuid):
    t_status = str(status_transfer(uuid).text)
    if "sip_uuid" in t_status:
        if db_handler(AppConstants.TRANSFER, AppConstants.UPDATE_SIP_UUID_TRANSFER, uuid, t_status["sip_uuid"]):
            return str(status_ingest(t_status["sip_uuid"]).text)
    else:
        return t_status


def update_source(id):
    return db_handler(AppConstants.SOURCE, AppConstants.UPDATE_STATUS_SOURCE, id)


def start_transfer_auto():
    # TODO: Bugfix get_active_transfer_db
    if len(get_active_transfers_db()) < 2:
        new_ingest = get_unstarted_source_from_db()
        r = start_transfer(new_ingest[1], new_ingest[2], new_ingest[0],
                           (str(AppConstants.SOURCE_DICT[new_ingest[2]]) + "/" + new_ingest[1]),
                           AppConstants.PROCESS_AUTOMATED)
        if r is not None:
            if r["status"] == 200:
                if update_source(new_ingest[0]):
                    write_logs("Update source was successful", "[INFO]")
                # TODO: Bugfix insert_transfer_db
                if insert_transfer_db(new_ingest[0], new_ingest[1], new_ingest[0], r["uuid"], AppConstants.PROCESSING,
                                      AppConstants.PROCESS_AUTOMATED):
                    write_logs("Update transfer in DB was successful", "[INFO]")
    else:
        sleep(5)
    pass


def init():
    list_db = get_sources_from_db()
    list_source = get_all_source_folder()
    compare_source_db(list_source, list_db)
    refresh_transfer_list_db()
    return


# TODO: Started Transfers have no entry in transfer table. Also check, if L131 works when problem with table is solved
if __name__ == "__main__":
    init()
    while True:
        start_transfer_auto()
        init()
    pass
