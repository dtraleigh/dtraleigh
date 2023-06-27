import os
from django.contrib.gis.utils import LayerMapping

from newBernTOD.models import NCOD, HOD

# Auto-generated `LayerMapping` dictionary for Overlay model
overlay_mapping = {
    'objectid': 'OBJECTID',
    'overlay': 'OVERLAY',
    'olay_decod': 'OLAY_DECOD',
    'olay_name': 'OLAY_NAME',
    'zone_case': 'ZONE_CASE',
    'ordinance': 'ORDINANCE',
    'eff_date': 'EFF_DATE',
    'overlay_ty': 'OVERLAY_TY',
    'shape_leng': 'SHAPE_Leng',
    'shape_area': 'SHAPE_Area',
    'geom': 'MULTIPOLYGON',
}

# Auto-generated `LayerMapping` dictionary for HOD model
hod_mapping = {
    'objectid': 'OBJECTID',
    'overlay': 'OVERLAY',
    'olay_decod': 'OLAY_DECOD',
    'olay_name': 'OLAY_NAME',
    'zone_case': 'ZONE_CASE',
    'ordinance': 'ORDINANCE',
    'eff_date': 'EFF_DATE',
    'overlay_ty': 'OVERLAY_TY',
    'shape_leng': 'SHAPE_Leng',
    'shape_area': 'SHAPE_Area',
    'geom': 'MULTIPOLYGON',
}

ncod_shp = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "resources", "Neighborhood_Conservation_Overlay_District_(-NCOD).shp"),
)

hod_g_shp = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "resources", "General_Historic_Overlay_District_(-HOD-G).shp"),
)

hod_s_shp = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "resources", "Streetside_Historic_Overlay_District_(-HOD-S).shp"),
)


def run_ncod_load(verbose=True):
    lm = LayerMapping(NCOD, ncod_shp, overlay_mapping, transform=False)
    lm.save(strict=True, verbose=verbose)


def run_hod_g_load(verbose=True):
    lm = LayerMapping(HOD, hod_g_shp, overlay_mapping, transform=False)
    lm.save(strict=True, verbose=verbose)


def run_hod_s_load(verbose=True):
    lm = LayerMapping(HOD, hod_s_shp, overlay_mapping, transform=False)
    lm.save(strict=True, verbose=verbose)
