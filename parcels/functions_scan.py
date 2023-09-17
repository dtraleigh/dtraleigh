def update_parcel_is_active(list_of_objectids_scanned, parcel_query_is_active_true):
    # Take parcels in the DB that have been marked active. If they aren't part of the scan, change them to False.
    for parcel in parcel_query_is_active_true:
        if parcel.objectid not in list_of_objectids_scanned:
            parcel.is_active = False
            parcel.save()
