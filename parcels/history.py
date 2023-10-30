def get_diff_between(new_record, old_record):
    delta = new_record.diff_against(old_record)
    return delta


def get_parcel_history_diffs(parcel_history):
    parcel_diff_list = []
    for count, parcel in enumerate(parcel_history):
        if count < len(parcel_history) - 1:
            new_record = parcel
            old_record = parcel_history[count + 1]
            parcel_diff_list.append(get_diff_between(new_record, old_record))

    return parcel_diff_list


def get_parcel_history_table_headers(parcel_history_diffs_list):
    headers = []
    for diff_object in parcel_history_diffs_list:
        headers += diff_object.changed_fields

    return list(set(headers))


def get_parcel_history_table_data(parcel_history_diffs_list, parcel_history_table_headers):
    table_data = []
    for diff_object in parcel_history_diffs_list:
        data_row = []
        for diff in diff_object.changes:
            []
