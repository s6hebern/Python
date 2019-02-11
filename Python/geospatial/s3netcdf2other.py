import os
import shutil
import subprocess as sub
from osgeo import gdal
from netCDF4 import Dataset

BANDNAMES = ['Oa{0}_radiance'.format(str(i).zfill(2)) for i in range(1, 22)]


def s3netcdf2other(input_dir, output_image, outformat='GTiff'):
    rad_tifs = []
    nc_paths = [os.path.join(input_dir, band + '.nc') for band in BANDNAMES]
    tempdir = os.path.join(input_dir, 'tmp')
    if os.path.exists(tempdir):
        shutil.rmtree(tempdir)
    os.mkdir(tempdir)
    # get lat/lon
    nc_coords = os.path.join(input_dir, 'geo_coordinates.nc')
    ds_nc = Dataset(nc_coords, 'r')
    coords = (ds_nc.variables['latitude'], ds_nc.variables['longitude'])
    for v, var in enumerate(coords):
        nodata = var._FillValue
        scale = var.scale_factor
        var_vrt = os.path.join(tempdir, var.name + '.vrt')
        var_tif = os.path.join(tempdir, var.name + '.tif')
        cmd = ['gdalbuildvrt', '-sd', str(2 + v), '-separate', '-overwrite', var_vrt, nc_coords]
        sub.call(cmd)
        # edit vrt
        with open(var_vrt, 'r') as f:
            xml = f.readlines()
        for line in xml:
            if '<VRTRasterBand ' in line:
                head_index = xml.index(line) + 1
            if '<DstRect xOff' in line:
                tail_index = xml.index(line) + 1
        xml.insert(head_index, '    <NoDataValue>{nd}</NoDataValue>\n'.format(nd=nodata))
        xml.insert(head_index + 1, '    <Scale>{sc}</Scale>\n'.format(sc=scale))
        tail_index = tail_index + 2
        xml.insert(tail_index, '      <NODATA>{nd}</NODATA>\n'.format(nd=nodata))
        xml.insert(tail_index + 2, '    <Offset>0.0</Offset>\n')
        xml.insert(tail_index + 3, '    <Scale>{sc}</Scale>\n'.format(sc=scale))
        xml = [line.replace('="Int32', '="Float32') for line in xml]
        with open(var_vrt, 'w') as f:
            f.writelines(xml)
        # write to temporary tif
        cmd = ['gdal_translate', '-unscale', var_vrt, var_tif]
        sub.call(cmd)
    ds_nc.close()
    lat_tif = os.path.join(tempdir, 'latitude.tif')
    lon_tif = os.path.join(tempdir, 'longitude.tif')
    # single bands to vrt, then to tif
    for nc in nc_paths:
        ds_nc = Dataset(nc, 'r')
        var = ds_nc.variables[os.path.basename(nc)[:-3]]
        nodata = var._FillValue
        offset = var.add_offset
        rows = var.shape[0]
        scale = var.scale_factor
        ds_nc.close()
        data_vrt = os.path.join(tempdir, 'data.vrt')
        data_vrt_tif = data_vrt.replace('.vrt', '.tif')
        if os.path.exists(data_vrt):
            os.remove(data_vrt)
        if os.path.exists(data_vrt_tif):
            os.remove(data_vrt_tif)
        out_vrt = os.path.join(tempdir, os.path.basename(nc)[:-3] + '.vrt')
        out_tif = out_vrt.replace('.vrt', '.tif')
        cmd = ['gdalbuildvrt', '-sd', '1', '-separate', '-overwrite', data_vrt, nc]
        sub.call(cmd)
        # edit vrt
        with open(data_vrt, 'r') as f:
            xml = f.readlines()
        for line in xml:
            if '<VRTRasterBand ' in line:
                head_index = xml.index(line)
            if '<DstRect xOff' in line:
                tail_index = xml.index(line) + 1
        xml[head_index] = '  <VRTRasterBand dataType="Float32" band="1">\n'
        xml.insert(head_index + 1, '    <NoDataValue>{nd}</NoDataValue>\n'.format(nd=nodata))
        xml[head_index + 2] = '    <ComplexSource>\n'
        xml[head_index + 5] = xml[head_index + 5].replace('DataType="UInt16"', 'DataType="Float32"')
        tail_index = tail_index + 1
        xml.insert(tail_index, '      <NODATA>{nd}</NODATA>\n'.format(nd=nodata))
        xml[tail_index + 1] = '    </ComplexSource>\n'
        xml.insert(tail_index + 2, '    <Offset>{off}</Offset>\n'.format(off=offset))
        xml.insert(tail_index + 3, '    <Scale>{sc}</Scale>\n'.format(sc=scale))
        with open(data_vrt, 'w') as f:
            f.writelines(xml)
        # write to temporary tif, then build a new vrt
        cmd = ['gdal_translate', '-unscale', data_vrt, data_vrt_tif]
        sub.call(cmd)
        # update GeoTransform
        ds = gdal.Open(data_vrt_tif, gdal.GA_Update)
        ds.SetGeoTransform((0.0, 1.0, 0.0, float(rows), 0.0, -1.0))
        ds.FlushCache()
        # build new vrt
        cmd = ['gdalbuildvrt', '-sd', '1', '-separate', '-overwrite', out_vrt, data_vrt_tif]
        sub.call(cmd)
        # edit vrt
        with open(out_vrt, 'r') as f:
            xml = f.readlines()
        for line in xml:
            if '<VRTRasterBand ' in line:
                head_index = xml.index(line)
                break
        xml[head_index] = '  <VRTRasterBand dataType="Float32" band="1">\n'
        xml.insert(-1, '''  <metadata domain="GEOLOCATION">
    <mdi key="X_DATASET">{lon}</mdi>
    <mdi key="X_BAND">1</mdi>
    <mdi key="Y_DATASET">{lat}</mdi>
    <mdi key="Y_BAND">1</mdi>
    <mdi key="PIXEL_OFFSET">0</mdi>
    <mdi key="LINE_OFFSET">0</mdi>
    <mdi key="PIXEL_STEP">1</mdi>
    <mdi key="LINE_STEP">1</mdi>
  </metadata>\n'''.format(lon=lon_tif, lat=lat_tif))
        for line in xml:
            if os.sep in line:
                xml[xml.index(line)] = line.replace(os.sep, '/')
        with open(out_vrt, 'w') as f:
            f.writelines(xml)
        # convert to tif
        cmd = ['gdalwarp', '-overwrite', '-t_srs', 'epsg:4326', '-geoloc', out_vrt, out_tif]
        sub.call(cmd)
        # remove temp files safely (somehow, Windows does not release the file correctly)
        os.remove(out_vrt)
        ds = gdal.Open(data_vrt_tif, gdal.GA_ReadOnly)
        ds = None
        os.remove(data_vrt_tif)
        rad_tifs.append(out_tif)
    # stack together
    cmd = ['python', r"c:\Program Files\GDAL\gdal_merge.py", '-separate', '-of', outformat, '-o', output_image]
    for r in rad_tifs:
        cmd.append(r)
    sub.call(cmd)
    shutil.rmtree(tempdir)

if __name__ == '__main__':
    indir = r'd:\s3\S3A_OL_1_EFR____20180402T093229_20180402T093529_20180403T155138_0179_029_307_1980_MAR_O_NT_002.SEN3'
    out = r'd:\s3\S3A_OL_1_EFR____20180402T093229_20180402T093529_20180403T155138_0179_029_307_1980_MAR_O_NT_002.SEN3\test.tif'
    of = 'GTiff'
    s3netcdf2other(indir, out, of)
