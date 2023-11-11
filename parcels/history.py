from parcels.models import Parcel


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


def is_valid_diff_to_show(diff_object, changed_field):
    unnecessary_fields = ["geom", "property_address"]
    if changed_field in unnecessary_fields:
        return False

    if Parcel._meta.get_field(changed_field).get_internal_type() == "CharField":
        parcel_instance = Parcel.objects.get(objectid=diff_object.old_record.objectid)
        values_across_changes = get_historical_values_per_field(parcel_instance.history.all(), changed_field)
        cleaned_values = list(set([x.strip() for x in values_across_changes]))
        if len(cleaned_values) == 1:
            return False

    return True


def get_parcel_history_table_headers(parcel_history_diffs_list):
    headers = []
    for diff_object in parcel_history_diffs_list:
        changed_fields = diff_object.changed_fields
        for changed_field in changed_fields:
            if is_valid_diff_to_show(diff_object, changed_field):
                headers.append(changed_field)

    return list(set(headers))


def get_historical_values_per_field(parcel_history, field_name):
    values_across_time = []
    for snapshot in parcel_history:
        values_across_time.append(getattr(snapshot, field_name))

    return values_across_time
