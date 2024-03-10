from django.test import TestCase

from parcels.history import get_parcel_history_diffs, get_parcel_history_table_headers
from parcels.models import Parcel, RaleighSubsection, ParcelHistorical, Snapshot
from parcels.parcel_archive.functions import identify_coordinate_system, convert_geometry_to_epsg4326, \
    verify_epsg4326_format, switch_coordinates
from parcels.management.commands._03_convert_coordinates import convert_and_save_new_geojson


class ParcelTestCase(TestCase):
    databases = "__all__"
    fixtures = ["parcels_test_data", "raleigh_subsections"]

    def setUp(self):
        Snapshot.objects.create(name="Test Snapshot")

    def test_get_parcel_history_table_headers1(self):
        prop1 = Parcel.objects.get(addr1="208 FREEMAN ST")
        parcel_history_diffs_list1 = get_parcel_history_diffs(prop1.history.all())

        self.assertEqual(get_parcel_history_table_headers(parcel_history_diffs_list1), ["bldg_val"])

        prop2 = Parcel.objects.get(objectid=350951)
        parcel_history_diffs_list2 = get_parcel_history_diffs(prop2.history.all())

        self.assertEqual(get_parcel_history_table_headers(parcel_history_diffs_list2), [])

        prop3 = Parcel.objects.get(objectid=205)
        parcel_history_diffs_list3 = get_parcel_history_diffs(prop3.history.all())

        self.assertEqual(get_parcel_history_table_headers(parcel_history_diffs_list3), ["owner"])

        prop4 = Parcel.objects.get(objectid=131225)
        parcel_history_diffs_list4 = get_parcel_history_diffs(prop4.history.all())

        self.assertEqual(get_parcel_history_table_headers(parcel_history_diffs_list4), [])

    def test_parcel_is_fully_in_or_out_of_a_subsection(self):
        test_subsection1 = RaleighSubsection.objects.get(id=186)
        test_subsection2 = RaleighSubsection.objects.get(id=190)

        data_geojson = {'type': 'Feature', 'geometry': {'type': 'Polygon', 'coordinates': [[[-78.62529430472327,
                                                                                             35.77710487969577],
                                                                                            [-78.62529430472327,
                                                                                             35.77689897602288],
                                                                                            [-78.62492947413203,
                                                                                             35.77689897602288],
                                                                                            [-78.62492947413203,
                                                                                             35.77710487969577],
                                                                                            [-78.62529430472327,
                                                                                             35.77710487969577]]]},
                        'properties': {}}
        freeman_parcel = ParcelHistorical.objects.create(data_geojson=data_geojson,
                                                         snapshot=Snapshot.objects.get(name="Test Snapshot"))

        self.assertTrue(freeman_parcel.get_geosgeom_object().intersects(test_subsection1.geom))
        self.assertFalse(freeman_parcel.get_geosgeom_object().intersects(test_subsection2.geom))

        # Get the query right
        overlapping_subsections = RaleighSubsection.objects.filter(
            geom__intersects=freeman_parcel.get_geosgeom_object())

        self.assertEqual([s.id for s in overlapping_subsections], [186])

    def test_parcel_overlaps_multiple_subsections(self):
        test_subsection1 = RaleighSubsection.objects.get(id=186)
        test_subsection2 = RaleighSubsection.objects.get(id=190)

        data_geojson = {'type': 'Feature', 'geometry': {'type': 'Polygon', 'coordinates': [[[-78.62983035930512,
                                                                                             35.77805532317532],
                                                                                            [-78.62914098450993,
                                                                                             35.77805532317532],
                                                                                            [-78.62914098450993,
                                                                                             35.77889549477342],
                                                                                            [-78.62983035930512,
                                                                                             35.77889549477342],
                                                                                            [-78.62983035930512,
                                                                                             35.77805532317532]]]},
                        'properties': {}}
        wym_academy_parcel = ParcelHistorical.objects.create(data_geojson=data_geojson,
                                                             snapshot=Snapshot.objects.get(name="Test Snapshot"))

        self.assertTrue(wym_academy_parcel.get_geosgeom_object().intersects(test_subsection1.geom))
        self.assertTrue(wym_academy_parcel.get_geosgeom_object().intersects(test_subsection2.geom))

        # Get the query right
        overlapping_subsections = RaleighSubsection.objects.filter(
            geom__intersects=wym_academy_parcel.get_geosgeom_object())

        self.assertEqual([s.id for s in overlapping_subsections], [186, 190])

    def test_identify_coordinate_system1(self):
        data_geojson = {'type': 'Feature', 'geometry': {'type': 'Polygon', 'coordinates': [[[-78.62983035930512,
                                                                                             35.77805532317532],
                                                                                            [-78.62914098450993,
                                                                                             35.77805532317532],
                                                                                            [-78.62914098450993,
                                                                                             35.77889549477342],
                                                                                            [-78.62983035930512,
                                                                                             35.77889549477342],
                                                                                            [-78.62983035930512,
                                                                                             35.77805532317532]]]},
                        'properties': {}}
        wym_academy_parcel = ParcelHistorical.objects.create(data_geojson=data_geojson,
                                                             snapshot=Snapshot.objects.get(name="Test Snapshot"))

        self.assertEquals(identify_coordinate_system(wym_academy_parcel), "epsg:4326")

    def test_identify_coordinate_system2(self):
        data_geojson = {'type': 'Feature', 'geometry': {'type': 'Polygon', 'coordinates': [
            [[2057700.658352524, 785763.0449847579], [2057793.5310565978, 785856.9683128446],
             [2057837.2041446418, 785813.7954488099], [2057838.4084340332, 785812.6163656209],
             [2057851.2390886545, 785801.3384888023], [2057852.9635046571, 785799.8603447974],
             [2057854.4989926666, 785798.5788087994], [2057856.04932867, 785797.3151927888],
             [2057857.6134886593, 785796.0694967955], [2057861.0776806623, 785794.0993207842],
             [2057783.673008591, 785680.9806006849], [2057700.658352524, 785763.0449847579]]]},
                        'properties': {}}
        test_parcel = ParcelHistorical.objects.create(data_geojson=data_geojson,
                                                      snapshot=Snapshot.objects.get(name="Test Snapshot"))

        self.assertEquals(identify_coordinate_system(test_parcel), "epsg:2264")

    def test_identify_coordinate_system3(self):
        # Note: geometry.type is missing and the lat, lons are reversed from how I want them to be.
        data_geojson = {'type': 'Feature', 'geometry': [[[35.88959578462791, -78.73211042127825],
                                                         [35.88959535879109, -78.73228935104193],
                                                         [35.88965304830429, -78.73228955914604],
                                                         [35.88965347414136, -78.73211062925463],
                                                         [35.88959578462791, -78.73211042127825]]],
                        'properties': {}}
        wym_academy_parcel = ParcelHistorical.objects.create(data_geojson=data_geojson,
                                                             snapshot=Snapshot.objects.get(name="Test Snapshot"))

        self.assertEquals(identify_coordinate_system(wym_academy_parcel), "epsg:4326")

    def test_convert_coordinates_to_epsg4326_polygon(self):
        data_geojson = {'type': 'Feature', 'geometry': {'type': 'Polygon', 'coordinates': [
            [[2057700.65835252404213, 785763.044984757900238], [2057793.531056597828865, 785856.968312844634056],
             [2057837.204144641757011, 785813.795448809862137], [2057838.408434033161029, 785812.616365620866418],
             [2057851.239088654518127, 785801.338488802313805], [2057852.963504657149315, 785799.860344797372818],
             [2057854.498992666602135, 785798.578808799386024], [2057856.049328669905663, 785797.31519278883934],
             [2057857.613488659262657, 785796.069496795535088], [2057861.077680662274361, 785794.099320784211159],
             [2057783.673008590936661, 785680.98060068488121], [2057700.65835252404213, 785763.044984757900238]]]},
                        'properties': {}}
        test_parcel = ParcelHistorical.objects.create(data_geojson=data_geojson,
                                                      snapshot=Snapshot.objects.get(name="Test Snapshot"))

        self.assertEquals(convert_geometry_to_epsg4326(test_parcel.data_geojson["geometry"]),
                          {'type': 'Polygon', 'coordinates': [
                              [[35.90881745682365, -78.80515335517815], [35.90907497918936, -78.80483911497788],
                               [35.90895613994314, -78.80469192411718], [35.908952894289534, -78.80468786524607],
                               [35.9089218426629, -78.80464461299543], [35.90891777262413, -78.80463879972656],
                               [35.9089142437226, -78.80463362313286], [35.90891076396983, -78.80462839628109],
                               [35.90890733337146, -78.80462312262917], [35.90890190222796, -78.80461143767371],
                               [35.90859156386521, -78.80487357231215], [35.90881745682365, -78.80515335517815]]]})

    def test_convert_coordinates_to_epsg4326_multipolygon(self):
        data_geojson = {'type': 'Feature', 'geometry': {'type': 'MultiPolygon', 'coordinates': [
            [[[2106530.2499499917, 749328.0000868291], [2106590.7499180585, 749356.1877348572],
              [2106586.4998060465, 749369.374806866], [2106584.4999340475, 749374.6873188764],
              [2106587.750110045, 749376.3748708665], [2106600.000222057, 749350.9376868457],
              [2106584.000222042, 749344.0625508428], [2106567.749854028, 749336.5622628331],
              [2106550.2502060086, 749328.0625508279], [2106547.500254005, 749326.3749988228],
              [2106544.4999340028, 749325.2501348257], [2106541.500126004, 749324.624982819],
              [2106538.499806002, 749324.4375908226], [2106537.000157997, 749324.5000548214],
              [2106534.749917999, 749325.0627428293], [2106532.50018999, 749326.3749988228],
              [2106530.2499499917, 749328.0000868291]]],
            [[[2106495.7498539686, 749287.8751587868], [2106493.5001259595, 749294.0002148002],
              [2106496.499933958, 749303.2500068098], [2106497.000157967, 749298.9486947954],
              [2106497.000157967, 749291.8124388009], [2106496.499933958, 749289.5627107918],
              [2106495.7498539686, 749287.8751587868]]]
        ]},
                        'properties': {}}
        test_parcel = ParcelHistorical.objects.create(data_geojson=data_geojson,
                                                      snapshot=Snapshot.objects.get(name="Test Snapshot"))

        self.assertEquals(convert_geometry_to_epsg4326(test_parcel.data_geojson["geometry"]),
                          {'type': 'MultiPolygon', 'coordinates': [
                              [[[35.80834807163083, -78.64070941475882], [35.80842490859484, -78.64050502629145],
                                [35.8084611791474, -78.64051919931747], [35.808475793876056, -78.64052587927993],
                                [35.80848039767987, -78.64051489700091], [35.80841039333176, -78.6404738925084],
                                [35.808391664753664, -78.64052793864448], [35.80837122118886, -78.64058283678894],
                                [35.80834804434928, -78.64064196047083], [35.80834343555912, -78.64065125565273],
                                [35.80834037510638, -78.64066138836341], [35.808338687484806, -78.64067151324603],
                                [35.80833820250656, -78.64068163451103], [35.808338389023604, -78.64068669151038],
                                [35.80833995724785, -78.64069427387454], [35.80834358472212, -78.64070184536229],
                                [35.80834807163083, -78.64070941475882]]],
                              [[[35.808238181141675, -78.64082626055878], [35.808255030605096, -78.64083377331494],
                                [35.80828041234025, -78.64082354320138], [35.808268590559756, -78.64082190861905],
                                [35.80824898543258, -78.64082199570178], [35.808242809824456, -78.64082371022475],
                                [35.808238181141675, -78.64082626055878]]]
                          ]})

    def test_switch_coordinates(self):
        # Test case with integer coordinates
        coordinates_int = [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        switched_coordinates_int = switch_coordinates(coordinates_int)
        self.assertEquals(switched_coordinates_int, [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]])

        # Test case with float coordinates
        coordinates_float = [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]]
        switched_coordinates_float = switch_coordinates(coordinates_float)
        self.assertEquals(switched_coordinates_float, [[[0.0, 0.0], [0.0, 1.0], [1.0, 1.0], [1.0, 0.0], [0.0, 0.0]]])

        # Test case with multiple polygons
        coordinates_multi_polygon = [
            [[[35.80834807163083, -78.64070941475882], [35.80842490859484, -78.64050502629145],
              [35.8084611791474, -78.64051919931747], [35.808475793876056, -78.64052587927993],
              [35.80848039767987, -78.64051489700091], [35.80841039333176, -78.6404738925084],
              [35.808391664753664, -78.64052793864448], [35.80837122118886, -78.64058283678894],
              [35.80834804434928, -78.64064196047083], [35.80834343555912, -78.64065125565273],
              [35.80834037510638, -78.64066138836341], [35.808338687484806, -78.64067151324603],
              [35.80833820250656, -78.64068163451103], [35.808338389023604, -78.64068669151038],
              [35.80833995724785, -78.64069427387454], [35.80834358472212, -78.64070184536229],
              [35.80834807163083, -78.64070941475882]]],
            [[[35.808238181141675, -78.64082626055878], [35.808255030605096, -78.64083377331494],
              [35.80828041234025, -78.64082354320138], [35.808268590559756, -78.64082190861905],
              [35.80824898543258, -78.64082199570178], [35.808242809824456, -78.64082371022475],
              [35.808238181141675, -78.64082626055878]]]
        ]
        switched_coordinates_multi_polygon = switch_coordinates(coordinates_multi_polygon)
        self.assertEquals(switched_coordinates_multi_polygon,
                          [[[[-78.64070941475882, 35.80834807163083], [-78.64050502629145, 35.80842490859484],
                             [-78.64051919931747, 35.8084611791474], [-78.64052587927993, 35.808475793876056],
                             [-78.64051489700091, 35.80848039767987], [-78.6404738925084, 35.80841039333176],
                             [-78.64052793864448, 35.808391664753664], [-78.64058283678894, 35.80837122118886],
                             [-78.64064196047083, 35.80834804434928], [-78.64065125565273, 35.80834343555912],
                             [-78.64066138836341, 35.80834037510638], [-78.64067151324603, 35.808338687484806],
                             [-78.64068163451103, 35.80833820250656], [-78.64068669151038, 35.808338389023604],
                             [-78.64069427387454, 35.80833995724785], [-78.64070184536229, 35.80834358472212],
                             [-78.64070941475882, 35.80834807163083]]],
                           [[[-78.64082626055878, 35.808238181141675], [-78.64083377331494, 35.808255030605096],
                             [-78.64082354320138, 35.80828041234025], [-78.64082190861905, 35.808268590559756],
                             [-78.64082199570178, 35.80824898543258], [-78.64082371022475, 35.808242809824456],
                             [-78.64082626055878, 35.808238181141675]]]]
                          )

        # Test case with empty input
        coordinates_empty = []
        switched_coordinates_empty = switch_coordinates(coordinates_empty)
        self.assertEquals(switched_coordinates_empty, [])

    def test_verify_epsg4326_format1(self):
        # Note: geometry.type is missing and the lat, lons are reversed from how I want them to be.
        data_geojson = {'type': 'Feature', 'geometry': [[[35.88959578462791, -78.73211042127825],
                                                         [35.88959535879109, -78.73228935104193],
                                                         [35.88965304830429, -78.73228955914604],
                                                         [35.88965347414136, -78.73211062925463],
                                                         [35.88959578462791, -78.73211042127825]]],
                        'properties': {}}
        wym_academy_parcel = ParcelHistorical.objects.create(data_geojson=data_geojson,
                                                             snapshot=Snapshot.objects.get(name="Test Snapshot"))
        expected_output = {'type': 'Polygon', 'coordinates': [[
            [-78.73211042127825, 35.88959578462791],
            [-78.73228935104193, 35.88959535879109],
            [-78.73228955914604, 35.88965304830429],
            [-78.73211062925463, 35.88965347414136],
            [-78.73211042127825, 35.88959578462791]]]}

        self.assertEquals(verify_epsg4326_format(wym_academy_parcel), expected_output)

    def test_convert_and_save_new_geojson1(self):
        # epsg:2264 polygon
        data_geojson = {'type': 'Feature', 'geometry': {'type': 'Polygon', 'coordinates': [
            [[2057700.658352524, 785763.0449847579], [2057793.5310565978, 785856.9683128446],
             [2057837.2041446418, 785813.7954488099], [2057838.4084340332, 785812.6163656209],
             [2057851.2390886545, 785801.3384888023], [2057852.9635046571, 785799.8603447974],
             [2057854.4989926666, 785798.5788087994], [2057856.04932867, 785797.3151927888],
             [2057857.6134886593, 785796.0694967955], [2057861.0776806623, 785794.0993207842],
             [2057783.673008591, 785680.9806006849], [2057700.658352524, 785763.0449847579]]]},
                        'properties': {}}
        test_parcel = ParcelHistorical.objects.create(data_geojson=data_geojson,
                                                      snapshot=Snapshot.objects.get(name="Test Snapshot"))
        convert_and_save_new_geojson(test_parcel, identify_coordinate_system(test_parcel))

        self.assertEquals(test_parcel.data_geojson,
                          {'type': 'Feature', 'geometry': {'type': 'Polygon', 'coordinates': [
                              [[35.90881745682365, -78.80515335517815], [35.90907497918936, -78.80483911497788],
                               [35.90895613994314, -78.80469192411718], [35.908952894289534, -78.80468786524607],
                               [35.9089218426629, -78.80464461299543], [35.90891777262413, -78.80463879972656],
                               [35.9089142437226, -78.80463362313286], [35.90891076396983, -78.80462839628109],
                               [35.90890733337146, -78.80462312262917], [35.90890190222796, -78.80461143767371],
                               [35.90859156386521, -78.80487357231215], [35.90881745682365, -78.80515335517815]]]},
                           'properties': {}})

    def test_convert_and_save_new_geojson2(self):
        # epsg:2264 multipolygon
        data_geojson = {'type': 'Feature', 'geometry': {'type': 'MultiPolygon', 'coordinates': [
            [[[2106530.2499499917, 749328.0000868291], [2106590.7499180585, 749356.1877348572],
              [2106586.4998060465, 749369.374806866], [2106584.4999340475, 749374.6873188764],
              [2106587.750110045, 749376.3748708665], [2106600.000222057, 749350.9376868457],
              [2106584.000222042, 749344.0625508428], [2106567.749854028, 749336.5622628331],
              [2106550.2502060086, 749328.0625508279], [2106547.500254005, 749326.3749988228],
              [2106544.4999340028, 749325.2501348257], [2106541.500126004, 749324.624982819],
              [2106538.499806002, 749324.4375908226], [2106537.000157997, 749324.5000548214],
              [2106534.749917999, 749325.0627428293], [2106532.50018999, 749326.3749988228],
              [2106530.2499499917, 749328.0000868291]]],
            [[[2106495.7498539686, 749287.8751587868], [2106493.5001259595, 749294.0002148002],
              [2106496.499933958, 749303.2500068098], [2106497.000157967, 749298.9486947954],
              [2106497.000157967, 749291.8124388009], [2106496.499933958, 749289.5627107918],
              [2106495.7498539686, 749287.8751587868]]]
        ]},
                        'properties': {}}
        test_parcel = ParcelHistorical.objects.create(data_geojson=data_geojson,
                                                      snapshot=Snapshot.objects.get(name="Test Snapshot"))
        convert_and_save_new_geojson(test_parcel, identify_coordinate_system(test_parcel))

        self.assertEquals(test_parcel.data_geojson,
                          {'type': 'Feature', 'geometry': {'type': 'MultiPolygon', 'coordinates': [
                              [[[35.80834807163083, -78.64070941475882], [35.80842490859484, -78.64050502629145],
                                [35.8084611791474, -78.64051919931747], [35.808475793876056, -78.64052587927993],
                                [35.80848039767987, -78.64051489700091], [35.80841039333176, -78.6404738925084],
                                [35.808391664753664, -78.64052793864448], [35.80837122118886, -78.64058283678894],
                                [35.80834804434928, -78.64064196047083], [35.80834343555912, -78.64065125565273],
                                [35.80834037510638, -78.64066138836341], [35.808338687484806, -78.64067151324603],
                                [35.80833820250656, -78.64068163451103], [35.808338389023604, -78.64068669151038],
                                [35.80833995724785, -78.64069427387454], [35.80834358472212, -78.64070184536229],
                                [35.80834807163083, -78.64070941475882]]],
                              [[[35.808238181141675, -78.64082626055878], [35.808255030605096, -78.64083377331494],
                                [35.80828041234025, -78.64082354320138], [35.808268590559756, -78.64082190861905],
                                [35.80824898543258, -78.64082199570178], [35.808242809824456, -78.64082371022475],
                                [35.808238181141675, -78.64082626055878]]]]},
                           'properties': {}})

    def test_convert_and_save_new_geojson3(self):
        # epsg:2264 type not specified
        data_geojson = {'type': 'Feature', 'geometry': [
            [[[2106530.2499499917, 749328.0000868291], [2106590.7499180585, 749356.1877348572],
              [2106586.4998060465, 749369.374806866], [2106584.4999340475, 749374.6873188764],
              [2106587.750110045, 749376.3748708665], [2106600.000222057, 749350.9376868457],
              [2106584.000222042, 749344.0625508428], [2106567.749854028, 749336.5622628331],
              [2106550.2502060086, 749328.0625508279], [2106547.500254005, 749326.3749988228],
              [2106544.4999340028, 749325.2501348257], [2106541.500126004, 749324.624982819],
              [2106538.499806002, 749324.4375908226], [2106537.000157997, 749324.5000548214],
              [2106534.749917999, 749325.0627428293], [2106532.50018999, 749326.3749988228],
              [2106530.2499499917, 749328.0000868291]]],
            [[[2106495.7498539686, 749287.8751587868], [2106493.5001259595, 749294.0002148002],
              [2106496.499933958, 749303.2500068098], [2106497.000157967, 749298.9486947954],
              [2106497.000157967, 749291.8124388009], [2106496.499933958, 749289.5627107918],
              [2106495.7498539686, 749287.8751587868]]]],
                        'properties': {}}
        test_parcel = ParcelHistorical.objects.create(data_geojson=data_geojson,
                                                      snapshot=Snapshot.objects.get(name="Test Snapshot"))
        convert_and_save_new_geojson(test_parcel, identify_coordinate_system(test_parcel))

        self.assertEquals(test_parcel.data_geojson,
                          {'type': 'Feature', 'geometry': {'type': 'MultiPolygon', 'coordinates': [
                              [[[35.80834807163083, -78.64070941475882], [35.80842490859484, -78.64050502629145],
                                [35.8084611791474, -78.64051919931747], [35.808475793876056, -78.64052587927993],
                                [35.80848039767987, -78.64051489700091], [35.80841039333176, -78.6404738925084],
                                [35.808391664753664, -78.64052793864448], [35.80837122118886, -78.64058283678894],
                                [35.80834804434928, -78.64064196047083], [35.80834343555912, -78.64065125565273],
                                [35.80834037510638, -78.64066138836341], [35.808338687484806, -78.64067151324603],
                                [35.80833820250656, -78.64068163451103], [35.808338389023604, -78.64068669151038],
                                [35.80833995724785, -78.64069427387454], [35.80834358472212, -78.64070184536229],
                                [35.80834807163083, -78.64070941475882]]],
                              [[[35.808238181141675, -78.64082626055878], [35.808255030605096, -78.64083377331494],
                                [35.80828041234025, -78.64082354320138], [35.808268590559756, -78.64082190861905],
                                [35.80824898543258, -78.64082199570178], [35.808242809824456, -78.64082371022475],
                                [35.808238181141675, -78.64082626055878]]]]},
                           'properties': {}})

    def test_convert_and_save_new_geojson4(self):
        # epsg:4326 polygon with points in the -78, 35 format as needed
        data_geojson = {'type': 'Feature', 'geometry': {'type': 'Polygon', 'coordinates': [
            [[-78.62983035930512, 35.77805532317532], [-78.62914098450993, 35.77805532317532],
             [-78.62914098450993, 35.77889549477342], [-78.62983035930512, 35.77889549477342],
             [-78.62983035930512, 35.77805532317532]]]},
                        'properties': {}}
        wym_academy_parcel = ParcelHistorical.objects.create(data_geojson=data_geojson,
                                                             snapshot=Snapshot.objects.get(name="Test Snapshot"))
        convert_and_save_new_geojson(wym_academy_parcel, identify_coordinate_system(wym_academy_parcel))

        self.assertEquals(wym_academy_parcel.data_geojson,
                          {'type': 'Feature', 'geometry': {'type': 'Polygon', 'coordinates':
                              [[[-78.62983035930512, 35.77805532317532], [-78.62914098450993, 35.77805532317532],
                                [-78.62914098450993, 35.77889549477342], [-78.62983035930512, 35.77889549477342],
                                [-78.62983035930512, 35.77805532317532]]]},
                           'properties': {}})

    def test_convert_and_save_new_geojson5(self):
        # epsg:4326 multipolygon with 35 and -78 format that needs to be switched
        data_geojson = {'type': 'Feature', 'geometry': {'type': 'MultiPolygon', 'coordinates': [
            [[[35.80834807163083, -78.64070941475882], [35.80842490859484, -78.64050502629145],
              [35.8084611791474, -78.64051919931747], [35.808475793876056, -78.64052587927993],
              [35.80848039767987, -78.64051489700091], [35.80841039333176, -78.6404738925084],
              [35.808391664753664, -78.64052793864448], [35.80837122118886, -78.64058283678894],
              [35.80834804434928, -78.64064196047083], [35.80834343555912, -78.64065125565273],
              [35.80834037510638, -78.64066138836341], [35.808338687484806, -78.64067151324603],
              [35.80833820250656, -78.64068163451103], [35.808338389023604, -78.64068669151038],
              [35.80833995724785, -78.64069427387454], [35.80834358472212, -78.64070184536229],
              [35.80834807163083, -78.64070941475882]]],
            [[[35.808238181141675, -78.64082626055878], [35.808255030605096, -78.64083377331494],
              [35.80828041234025, -78.64082354320138], [35.808268590559756, -78.64082190861905],
              [35.80824898543258, -78.64082199570178], [35.808242809824456, -78.64082371022475],
              [35.808238181141675, -78.64082626055878]]]]},
                        'properties': {}}
        test_parcel = ParcelHistorical.objects.create(data_geojson=data_geojson,
                                                      snapshot=Snapshot.objects.get(name="Test Snapshot"))
        convert_and_save_new_geojson(test_parcel, identify_coordinate_system(test_parcel))

        self.assertEquals(test_parcel.data_geojson,
                          {'type': 'Feature', 'geometry': {'type': 'MultiPolygon', 'coordinates': [
                              [[[-78.64070941475882, 35.80834807163083], [-78.64050502629145, 35.80842490859484],
                                [-78.64051919931747, 35.8084611791474], [-78.64052587927993, 35.808475793876056],
                                [-78.64051489700091, 35.80848039767987], [-78.6404738925084, 35.80841039333176],
                                [-78.64052793864448, 35.808391664753664], [-78.64058283678894, 35.80837122118886],
                                [-78.64064196047083, 35.80834804434928], [-78.64065125565273, 35.80834343555912],
                                [-78.64066138836341, 35.80834037510638], [-78.64067151324603, 35.808338687484806],
                                [-78.64068163451103, 35.80833820250656], [-78.64068669151038, 35.808338389023604],
                                [-78.64069427387454, 35.80833995724785], [-78.64070184536229, 35.80834358472212],
                                [-78.64070941475882, 35.80834807163083]]],
                              [[[-78.64082626055878, 35.808238181141675], [-78.64083377331494, 35.808255030605096],
                                [-78.64082354320138, 35.80828041234025], [-78.64082190861905, 35.808268590559756],
                                [-78.64082199570178, 35.80824898543258], [-78.64082371022475, 35.808242809824456],
                                [-78.64082626055878, 35.808238181141675]]]]},
                           'properties': {}})

    def test_convert_and_save_new_geojson6(self):
        # epsg:4326 type not specified
        data_geojson = {'type': 'Feature', 'geometry': [
            [[-78.62983035930512, 35.77805532317532], [-78.62914098450993, 35.77805532317532],
             [-78.62914098450993, 35.77889549477342], [-78.62983035930512, 35.77889549477342],
             [-78.62983035930512, 35.77805532317532]]],
                        'properties': {}}
        wym_academy_parcel = ParcelHistorical.objects.create(data_geojson=data_geojson,
                                                             snapshot=Snapshot.objects.get(name="Test Snapshot"))
        convert_and_save_new_geojson(wym_academy_parcel, identify_coordinate_system(wym_academy_parcel))

        self.assertEquals(wym_academy_parcel.data_geojson,
                          {'type': 'Feature', 'geometry': {'type': 'Polygon', 'coordinates':
                              [[[-78.62983035930512, 35.77805532317532], [-78.62914098450993, 35.77805532317532],
                                [-78.62914098450993, 35.77889549477342], [-78.62983035930512, 35.77889549477342],
                                [-78.62983035930512, 35.77805532317532]]]},
                           'properties': {}})
