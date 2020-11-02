import shutil
from os.path import exists as _exists
from os.path import split as _split
import datetime
from time import sleep
from copy import deepcopy

from wepppy.climates.cligen import ClimateFile
from wepppy.wepp.soils.utils import modify_kslast
from wepppy.nodb import *
from os.path import join as _join
from wepppy.wepp.out import TotalWatSed
from wepppy.export import arc_export

from wepppy.nodb.mods.locations.portland import LivnehDataManager
from wepppy.nodb.mods.locations.portland import ShallowLandSlideSusceptibility, BullRunBedrock

from osgeo import gdal

gdal.UseExceptions()

os.chdir('/geodata/weppcloud_runs/')

lvdm = LivnehDataManager()

# Run 1 - Daymet (adjust for <2005 and runoff/pp ratio) + shallow groundwater + pmetpara
# Run 2 - Daymet (adjust for <2005 and runoff/pp ratio) + shallow landslides + pmetpara
# Run 3 - GridMet (adjust for runoff/pp ratio) + shallow groundwater + pmetpara
# Run 4 - GridMet (adjust for runoff/pp ratio) + shallow landslides + pmetpara

precip_transforms = {
    'gridmet': {
        'SmallTest': 1.068883117,
        'SouthFork': 1.068883117,
        'CedarCreek': 1.120768995,
        'BlazedAlder': 1.098866242,
        'FirCreek': 0.916802717,
        'BRnearMultnoma': 1.180931876,
        'NorthFork': 1.267197533,
        'LittleSandy': 1.007254747,
    },
    'daymet': {
        'SmallTest': 1.100579816,
        'SouthFork': 1.100579816,
        'CedarCreek': 1.221992293,
        'BlazedAlder': 1.067938504,
        'FirCreek': 0.885748368,
        'BRnearMultnoma': 1.254837877,
        'NorthFork': 1.180883364,
        'LittleSandy': 1.008756432,
    }
}


def _daymet_cli_adjust(cli_dir, cli_fn, watershed_name):
    cli = ClimateFile(_join(cli_dir, cli_fn))

    cli.discontinuous_temperature_adjustment(datetime.date(2005, 11, 2))

    pp_scale = precip_transforms['daymet'][watershed_name]
    cli.transform_precip(offset=0, scale=pp_scale)

    cli.write(_join(cli_dir, 'adj_' + cli_fn))

    return 'adj_' + cli_fn


def _gridmet_cli_adjust(cli_dir, cli_fn, watershed_name):
    cli = ClimateFile(_join(cli_dir, cli_fn))

    pp_scale = precip_transforms['gridmet'][watershed_name]
    cli.transform_precip(offset=0, scale=pp_scale)

    cli.write(_join(cli_dir, 'adj_' + cli_fn))

    return 'adj_' + cli_fn


if __name__ == '__main__':
    projects = [
                  dict(wd='SmallTest',
                       extent=[-121.9716739654541, 45.38934878553456, -121.91159248352052, 45.431527384351135],
                       map_center=[-121.94163322448732, 45.41044202220255],
                       map_zoom=14,
                       outlet=[-121.93974494934083, 45.409598443927182],
                       landuse=None,
                       cs=50, erod=0.000001,
                       csa=5, mcl=65),
                #   dict(wd='SouthFork',
                #        extent=[-122.22908020019533, 45.268121280142886, -121.74842834472658, 45.60539133629575],
                #        map_center=[-121.98875427246095, 45.43700828867391],
                #        map_zoom=11,
                #        outlet=[-122.1083333, 45.444722],
                #        landuse=None,
                #        cs=50, erod=0.000001,
                #        csa=5, mcl=65),
                #   dict(wd='CedarCreek',
                #        extent=[-122.22908020019533, 45.268121280142886, -121.74842834472658, 45.60539133629575],
                #        map_center=[-121.98875427246095, 45.43700828867391],
                #        map_zoom=11,
                #        outlet=[-122.03486546021158, 45.45789702345389],
                #        landuse=None,
                #        cs=50, erod=0.000001,
                #        csa=5, mcl=65),
                #   dict(wd='BlazedAlder',
                #        extent=[-122.22908020019533, 45.268121280142886, -121.74842834472658, 45.60539133629575],
                #        map_center=[-121.98875427246095, 45.43700828867391],
                #        map_zoom=11,
                #        outlet=[-121.89124077457025, 45.45220046527376],
                #        landuse=None,
                #        cs=50, erod=0.000001,
                #        csa=5, mcl=65),
                #  dict(wd='FirCreek',
                #        extent=[-122.22908020019533, 45.268121280142886, -121.74842834472658, 45.60539133629575],
                #        map_center=[-121.98875427246095, 45.43700828867391],
                #        map_zoom=11,
                #        outlet=[-122.02581486422827, 45.47989113970676],
                #        landuse=None,
                #        cs=50, erod=0.000001,
                #        csa=5, mcl=65),
                #  dict(wd='BRnearMultnoma',
                #        extent=[-122.22908020019533, 45.268121280142886, -121.74842834472658, 45.60539133629575],
                #        map_center=[-121.98875427246095, 45.43700828867391],
                #        map_zoom=11,
                #        outlet=[-122.01099283401598, 45.498468197226025],
                #        landuse=None,
                #        cs=50, erod=0.000001,
                #        csa=10, mcl=100),
                # dict(wd='NorthFork',
                #      extent=[-122.22908020019533, 45.268121280142886, -121.74842834472658, 45.60539133629575],
                #      map_center=[-121.98875427246095, 45.43700828867391],
                #      map_zoom=11,
                #      outlet=[-122.03554486123724, 45.49455561832556],
                #      landuse=None,
                #      cs=50, erod=0.000001,
                #       csa=10, mcl=100),
                # dict(wd='LittleSandy',
                #       extent=[-122.22908020019533, 45.268121280142886, -121.74842834472658, 45.60539133629575],
                #       map_center=[-121.98875427246095, 45.43700828867391],
                #       map_zoom=11,
                #       outlet=[-122.17147271631961, 45.415421615033246],
                #       landuse=None,
                #       cs=50, erod=0.000001,
                #       csa=10, mcl=100)
               ]


    # for new run
    # dict(clean=True, build_soils=True, build_landuse=True, build_climates=True)
    #
    # setting clean to True deletes the project and re-delineates the watershed.
    # after built set clean to False
    #

    scenarios = {
        # 'daymet_groundwater_pmetpara':
        #     dict(clean=True, build_soils=True, build_landuse=True, build_climates=True),
        # 'daymet_landslides_pmetpara':
        #     dict(clean=True, build_soils=True, build_landuse=True, build_climates=True),
        #'gridmet_groundwater.2_pmetpara':
        #    dict(clean=False, build_soils=True, build_landuse=False, build_climates=False),
        'gridmet_grwlnd.2_pmetpara':
            dict(clean=False, build_soils=True, build_landuse=False, build_climates=False),
        # 'gridmet_landslides_pmetpara':
        #     dict(clean=True, build_soils=True, build_landuse=True, build_climates=True),
    }


    config = 'portland.cfg'
    top_pars = ((10, 100), )
    erod_pars = ((10, 1e-6), )
    for proj in projects:
        watershed_name = proj['wd']
        extent = proj['extent']
        map_center = proj['map_center']
        map_zoom = proj['map_zoom']
        outlet = proj['outlet']
        default_landuse = proj['landuse']

        for scenario in scenarios:
            clean = scenarios[scenario]['clean']
            build_soils = scenarios[scenario]['build_soils']
            build_landuse = scenarios[scenario]['build_landuse']
            build_climates = scenarios[scenario]['build_climates']

            for csa, mcl in top_pars:
                for cs, erod in erod_pars:
                    wd = 'portland_{watershed_name}_{scenario}_csa{csa}_mcl{mcl}_cs{cs}_erod{erod}'\
                         .format(watershed_name=watershed_name, scenario=scenario, csa=csa, mcl=mcl, cs=cs, erod=erod)

                    print(wd)

                    if clean:
                        if _exists(wd):
                            shutil.rmtree(wd)
                        os.mkdir(wd)

                        ron = Ron(wd, config)
                        ron.name = wd
                        ron.set_map(extent, map_center, zoom=map_zoom)
                        ron.fetch_dem()

                        print('building channels')
                        topaz = Topaz.getInstance(wd)
                        topaz.build_channels(csa=csa, mcl=mcl)
                        topaz.set_outlet(*outlet)
                        sleep(0.5)

                        print('building subcatchments')
                        topaz.build_subcatchments()

                        print('abstracting watershed')
                        watershed = Watershed.getInstance(wd)
                        watershed.abstract_watershed()
                        translator = watershed.translator_factory()
                        topaz_ids = [top.split('_')[1] for top in translator.iter_sub_ids()]

                    else:
                        ron = Ron.getInstance(wd)
                        topaz = Topaz.getInstance(wd)
                        watershed = Watershed.getInstance(wd)

                    landuse = Landuse.getInstance(wd)
                    if build_landuse:
                        landuse.mode = LanduseMode.Gridded
                        landuse.build()
                        landuse = Landuse.getInstance(wd)

                        print('setting default landuses')
                        # 105 - Tahoe High severity fire
                        # topaz_ids is a list of string ids e.g. ['22', '23']
                        if default_landuse is not None:
                            landuse.modify(topaz_ids, default_landuse)

                    soils = Soils.getInstance(wd)
                    if build_soils:
                        print('building soils')
                        soils.mode = SoilsMode.Gridded
                        soils.build()

                        print('adjusting restrictive layer ksat')
                        ksat_mod = None

                        _landslide = ShallowLandSlideSusceptibility()
                        _bedrock = BullRunBedrock()

                        if 'landslide' in scenario:
                            ksat_mod = 'l'
                        elif 'groundwater' in scenario:
                            ksat_mod = 'g'
                        elif 'grwlnd' in scenario:
                            ksat_mod = 'h'

                        _domsoil_d = soils.domsoil_d
                        _soils = soils.soils
                        for topaz_id, ss in watershed._subs_summary.items():
                            lng, lat = ss.centroid.lnglat

                            if ksat_mod == 'l':
                                _landslide_pt = _landslide.get_bedrock(lng, lat)
                                ksat = _landslide_pt['ksat']
                                name = _landslide_pt['Unit_Name'].replace(' ', '_')

                            elif ksat_mod == 'g':
                                _bedrock_pt = _bedrock.get_bedrock(lng, lat)
                                ksat = _bedrock_pt['ksat']
                                name = _bedrock_pt['Unit_Name'].replace(' ', '_')
                            else:
                                _landslide_pt = _landslide.get_bedrock(lng, lat)
                                _landslide_pt_ksat = _landslide_pt['ksat']

                                _bedrock_pt = _bedrock.get_bedrock(lng, lat)
                                _bedrock_pt_ksat = _bedrock_pt['ksat']
                                ksat = _landslide_pt_ksat
                                name = _landslide_pt['Unit_Name'].replace(' ', '_')

                                if isfloat(_bedrock_pt_ksat):
                                    ksat = _bedrock_pt_ksat
                                    name = _bedrock_pt['Unit_Name'].replace(' ', '_')

                            dom = _domsoil_d[str(topaz_id)]
                            _soil = deepcopy(_soils[dom])

                            _dom = '{dom}-{ksat_mod}_{bedrock_name}'\
                                   .format(dom=dom, ksat_mod=ksat_mod, bedrock_name=name)
                            if _dom not in _soils:
                                _soil_fn = '{dom}.sol'.format(dom=_dom)
                                src_soil_fn = _join(_soil.soils_dir, _soil.fname)
                                dst_soil_fn = _join(_soil.soils_dir, _soil_fn)
                                print(src_soil_fn, dst_soil_fn, ksat, _dom)
                                modify_kslast(src_soil_fn, dst_soil_fn, ksat)

                                _soil.fname = _soil_fn
                                _soils[_dom] = _soil

                            _domsoil_d[str(topaz_id)] = _dom

                        soils.lock()
                        soils.domsoil_d = _domsoil_d
                        soils.soils = _soils
                        soils.dump_and_unlock()
                        soils = Soils.getInstance(wd)

                    climate = Climate.getInstance(wd)
                    if build_climates:
                        print('building climate')
                        if 'linveh' in scenario:
                            climate.climate_mode = ClimateMode.ObservedDb
                            climate.climate_spatialmode = ClimateSpatialMode.Multiple
                            climate.input_years = 21

                            climate.lock()
                            lng, lat = watershed.centroid

                            cli_path = lvdm.closest_cli(lng, lat)
                            _dir, cli_fn = _split(cli_path)
                            shutil.copyfile(cli_path, _join(climate.cli_dir, cli_fn))
                            climate.cli_fn = cli_fn

                            par_path = lvdm.par_path
                            _dir, par_fn = _split(par_path)
                            shutil.copyfile(par_path, _join(climate.cli_dir, par_fn))
                            climate.par_fn = par_fn

                            sub_par_fns = {}
                            sub_cli_fns = {}
                            for topaz_id, ss in watershed._subs_summary.items():
                                print(topaz_id)
                                lng, lat = ss.centroid.lnglat

                                cli_path = lvdm.closest_cli(lng, lat)
                                _dir, cli_fn = _split(cli_path)
                                run_cli_path = _join(climate.cli_dir, cli_fn)
                                if not _exists(run_cli_path):
                                    shutil.copyfile(cli_path, run_cli_path)
                                sub_cli_fns[topaz_id] = cli_fn
                                sub_par_fns[topaz_id] = par_fn

                            climate.sub_par_fns = sub_par_fns
                            climate.sub_cli_fns = sub_cli_fns
                            climate.dump_and_unlock()

                        elif 'daymet' in scenario:
                            stations = climate.find_closest_stations()
                            climate.climatestation = stations[0]['id']

                            climate.climate_mode = ClimateMode.Observed
                            climate.climate_spatialmode = ClimateSpatialMode.Multiple
                            climate.set_observed_pars(start_year=1990, end_year=2017)

                            climate.build(verbose=1)

                            climate.lock()

                            cli_dir = climate.cli_dir
                            adj_cli_fn = _daymet_cli_adjust(cli_dir, climate.cli_fn, watershed_name)
                            climate.cli_fn = adj_cli_fn

                            for topaz_id in climate.sub_cli_fns:
                                adj_cli_fn = _daymet_cli_adjust(cli_dir, climate.sub_cli_fns[topaz_id], watershed_name)
                                climate.sub_cli_fns[topaz_id] = adj_cli_fn

                            climate.dump_and_unlock()

                        elif 'gridmet' in scenario:
                            stations = climate.find_closest_stations()
                            climate.climatestation = stations[0]['id']

                            climate.climate_mode = ClimateMode.GridMetPRISM
                            climate.climate_spatialmode = ClimateSpatialMode.Multiple
                            climate.set_observed_pars(start_year=1990, end_year=2017)

                            climate.build(verbose=1)

                            climate.lock()

                            cli_dir = climate.cli_dir
                            adj_cli_fn = _gridmet_cli_adjust(cli_dir, climate.cli_fn, watershed_name)
                            climate.cli_fn = adj_cli_fn

                            for topaz_id in climate.sub_cli_fns:
                                adj_cli_fn = _gridmet_cli_adjust(cli_dir, climate.sub_cli_fns[topaz_id], watershed_name)
                                climate.sub_cli_fns[topaz_id] = adj_cli_fn

                            climate.dump_and_unlock()

                    # build a climate for the channels.

                    print('running wepp')
                    wepp = Wepp.getInstance(wd)
                    wepp.prep_hillslopes()
                    wepp.run_hillslopes()

                    wepp = Wepp.getInstance(wd)
                    wepp.prep_watershed(erodibility=erod, critical_shear=cs, pmet=True)
                    wepp.run_watershed()
                    loss_report = wepp.report_loss()

                    print('running wepppost')
                    fn = _join(ron.export_dir, 'totalwatsed.csv')

                    totwatsed = TotalWatSed(_join(ron.output_dir, 'totalwatsed.txt'),
                                            wepp.baseflow_opts, wepp.phosphorus_opts)
                    totwatsed.export(fn)
                    assert _exists(fn)

                    arc_export(wd)
