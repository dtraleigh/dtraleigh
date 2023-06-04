import os
from django.contrib.gis.utils import LayerMapping
from develop.models import WakeCorporate, DevelopmentPlan

# Auto-generated `LayerMapping` dictionary for WakeCorporate model
wakecorporate_mapping = {
    "objectid": "OBJECTID",
    "short_name": "SHORT_NAME",
    "long_name": "LONG_NAME",
    "ordinance_field": "ORDINANCE_",
    "effective_field": "EFFECTIVE_",
    "shapearea": "SHAPEAREA",
    "shapelen": "SHAPELEN",
    "geom": "MULTIPOLYGON",
}

# Auto-generated `LayerMapping` dictionary for DevelopmentPlan model
developmentplan_mapping = {
    "objectid": "OBJECTID",
    "devplan_id": "devplan_id",
    "submitted": "submitted",
    "submitted_field": "submitted_",
    "approved": "approved",
    "daystoappr": "daystoappr",
    "plan_type": "plan_type",
    "status": "status",
    "appealperi": "appealperi",
    "updated": "updated",
    "sunset_dat": "sunset_dat",
    "acreage": "acreage",
    "major_stre": "major_stre",
    "cac": "cac",
    "engineer": "engineer",
    "engineer_p": "engineer_p",
    "developer": "developer",
    "developer_field": "developer_",
    "plan_name": "plan_name",
    "planurl": "planurl",
    "planurl_ap": "planurl_ap",
    "planner": "planner",
    "lots_req": "lots_req",
    "lots_rec": "lots_rec",
    "lots_apprv": "lots_apprv",
    "sq_ft_req": "sq_ft_req",
    "units_appr": "units_appr",
    "units_req": "units_req",
    "zoning": "zoning",
    "plan_numbe": "plan_numbe",
    "creationda": "CreationDa",
    "creator": "Creator",
    "editdate": "EditDate",
    "editor": "Editor",
    "geom": "MULTIPOINT",
}


wake_shp = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "Corporate_Limits", "Corporate_Limits.shp"),
)

devs_shp = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "Development_Plans", "Development_Plans.shp"),
)


def run_wake(verbose=True):
    lm = LayerMapping(WakeCorporate, wake_shp, wakecorporate_mapping, transform=False)
    lm.save(strict=True, verbose=verbose)


def run_devs(verbose=True):
    lm = LayerMapping(DevelopmentPlan, devs_shp, developmentplan_mapping, transform=False)
    lm.save(strict=True, verbose=verbose)
