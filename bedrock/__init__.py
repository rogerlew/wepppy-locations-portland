import os
import csv
from os.path import join as _join
import warnings
from osgeo import ogr

from wepppy.all_your_base import RasterDatasetInterpolator, RDIOutOfBoundsException, isfloat

_thisdir = os.path.dirname(__file__)

"""
> gdal_rasterize -l Bedrock -a OBJECTID -tr 30.0 30.0 -a_nodata 0.0 -te 862644.9015748054 1331481.7965879291 977244.4967191529 1395676.03969816 -ot Byte -of GTiff -at Bedrock.shp Bedrock.tif
> gdalwarp  -t_srs EPSG:26910 -r near -of vrt Bedrock.tif Bedrock_utm.vrt
> gdal_translate -co compress=LZW Bedrock_utm.vrt Bedrock_utm.tif
"""


class BullRunBedrock(object):
    def __init__(self):
        with open(_join(_thisdir, 'Bedrock_attrs.csv')) as fp:
            csv_rdr = csv.DictReader(fp)
            d = {}
            for row in csv_rdr:
                ksat = row['ksat']
                if isfloat(ksat):
                    ksat = float(ksat)
                else:
                    ksat = None
                row['ksat'] = ksat
                row['Shape_Leng'] = float(row['Shape_Leng'])
                row['Shape_Area'] = float(row['Shape_Area'])
                row['OBJECTID'] = int(row['OBJECTID'])
                d[row['OBJECTID']] = row

            self._d = d

    def get_bedrock(self, lng, lat):
        try:
            rdi = RasterDatasetInterpolator(_join(_thisdir, 'Bedrock_utm.tif'))
            object_id = rdi.get_location_info(lng, lat, method='nearest')
            return self._d[object_id]
        except RDIOutOfBoundsException:
            return self._d[0]


class ShallowLandSlideSusceptibility(object):
    def __init__(self):
        with open(_join(_thisdir, 'shallow_landslided_attrs.csv')) as fp:
            csv_rdr = csv.DictReader(fp)
            d = {}
            for row in csv_rdr:
                ksat = row['ksat']
                if isfloat(ksat):
                    ksat = float(ksat)
                else:
                    ksat = None
                row['ksat'] = ksat
                try:
                    row['OBJECTID'] = int(row['OBJECTID'])
                except:
                    row['OBJECTID'] = None
                d[row['OBJECTID']] = row

            self._d = d

    def get_bedrock(self, lng, lat):
        try:
            rdi = RasterDatasetInterpolator(_join(_thisdir, 'Shallow_Landslide_Susceptibility_utm.tif'))
            object_id = rdi.get_location_info(lng, lat, method='nearest')
            return self._d[object_id]
        except RDIOutOfBoundsException:
            return self._d[0]



if __name__ == "__main__":
    bullrun_bedrock = BullRunBedrock()
    print(bullrun_bedrock.get_bedrock(-121.88436270034585, 45.45078330129854))

# +proj=lcc +lat_1=43 +lat_2=45.5 +lat_0=41.75 +lon_0=-120.5 +x_0=399999.9999999999 +y_0=0 +datum=NAD83 +units=ft +no_defs
# +proj=lcc +lat_1=43 +lat_2=45.5 +lat_0=41.75 +lon_0=-120.5 +x_0=399999.9999999999 +y_0=0 +datum=NAD83 +units=ft +no_defs
# +proj=lcc +lat_1=43 +lat_2=45.5 +lat_0=41.75 +lon_0=-120.5 +x_0=399999.9999999999 +y_0=0 +datum=NAD83 +units=ft +no_defs
