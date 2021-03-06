#!/usr/bin/env python
import argparse
import copy
import glob
import itertools
import json
import os
import os.path
import re

import tqdm

from data_conversion.coverage import (
    gen_tif_metadata,
    gen_tif_coverage,
    get_coverage_extent,
    gen_coverage_uuid,
    gen_dataset_coverage,
)

# TODO: need to add resolution to data.json metadata
#       or just to dataset metadata ... probably more appropriate

# TODO: add mimetype somehwere?

CATEGORY = 'climate'
RESOLUTION = '2.5 arcmin'
SWIFT_CONTAINER = (
    'https://swift.rc.nectar.org.au/v1/AUTH_0bc40c2c2ff94a0b9404e6f960ae5677/'
    'australia_5km_layers'
)

RESOLUTIONS = {  # udunits arc_minute / arcmin, UCUM/UOM: min_arc
    '2.5 arcmin': '2.5 arcmim (~5km)',
}

DATASETS = [
    # current
    {
        # bio
        'title': 'Australia, Current Climate (1976-2005), {resolution}',
        'acknowledgement': (
            'Jones, D. A., Wang, W., & Fawcett, R. (2009). High-quality spatial '
            'climate data-sets for Australia. Australian Meteorological and '
            'Oceanographic Journal, 58(4), 233.'
        ),
        'filter': {
            'genre': 'DataGenreCC'
        },
        'aggs': [],
    },
    {
        'title': 'Australia, Climate Projection, {emsc} based on {gcm}, {resolution} - {year}',
        'acknowledgement': (
            'Vanderwal, Jeremy. (2012). All future climate layers for Australia - 5km '
            'resolution. James Cook University. [Data files] '
            'jcu.edu.au/tdh/collection/633b4ccd-2e78-459d-963c-e43d3c8a5ca1'
        ),
        'external_url': (
            'http://wallaceinitiative.org/climate_2012/tdhtools/Search/'
            'DataDownload.php?coverage=australia-5km'
        ),
        'license': (
            'Creative Commons Attribution 3.0 AU '
            'http://creativecommons.org/licenses/by/3.0/au'
        ),
        'filter': {
            'genre': 'DataGenreFC',
            'gcm': None,
            'emsc': None,
            'year': None
        },
        'aggs': [],
    }
]

COLLECTION = {
    "_type": "Collection",
    "uuid": "1db9e574-2f14-11e9-b0ea-0242ac110002",
    "title": "Australia current and future climate data",
    "description": "Current and future climate data for the Australian continent\n\nGeographic extent: Australia\nYear range: 1976-2005, 2015-2085\nResolution: 30 arcsec (~1 km), 2.5 arcmin (~5 km)\nData layers: B01-19",
    "rights": "CC-BY Attribution 3.0",
    "landingPage": "See <a href=\"https://research.jcu.edu.au/researchdata/default/detail/a06a78f553e1452bcf007231f6204f04/\">https://research.jcu.edu.au/researchdata/default/detail/a06a78f553e1452bcf007231f6204f04/</a>",
    "attribution": ["Vanderwal, Jeremy. (2012). All future climate layers for Australia - 5km resolution. James Cook University."],
    "subjects": ["Current datasets", "Future datasets"],
    "categories": ["climate"],
    "datasets": [
        # {
        #     "uuid": "8f6e3ea5-1caf-5562-a580-aa23bbe7c975",
        #     "title": "Australia, Current Climate (1976-2005), 2.5 arcmin (~5 km)"
        # },
        # {
        #     "uuid": "fecc0b23-4199-5b49-ac6c-45c3c1249f3e",
        #     "title": "Australia, Climate Projection, 2.5 arcmin"
        # }
    ],

    "BCCDataGenre": ["DataGenreCC", "DataGenreFC"]
}


def gen_dataset_metadata(dsdef, coverages, **kw):
    ds_md = {
        'category': CATEGORY,
        'genre': kw['genre'],
        'resolution': RESOLUTION,
        'acknowledgement': dsdef.get('acknowledgment'),
        'external_url': dsdef.get('external_url'),
        'license': dsdef.get('license'),
        # TODO: format title
        'title': dsdef['title'].format(resolution=RESOLUTIONS[RESOLUTION], **kw)
    }
    # collect some bits of metadata from data
    if dsdef['filter']['genre'] == 'DataGenreCC':
        # all coverages have the same year and year_range
        ds_md['year'] = coverages[0]['bccvl:metadata']['year']
        ds_md['year_range'] = coverages[0]['bccvl:metadata']['year_range']
    if dsdef['filter'].get('year'):
        # this is future?
        ds_md['gcm'] = dsdef['filter']['gcm']
        ds_md['emsc'] = dsdef['filter']['emsc']
        ds_md['year'] = coverages[0]['bccvl:metadata']['year']
        ds_md['year_range'] = coverages[0]['bccvl:metadata']['year_range']
    return ds_md


# TODO: duplicate in worldclim/generate_metadata_layers
def match_coverage(cov, attrs):
    # used to filter set of coverages
    md = cov['bccvl:metadata']
    for attr, value in attrs.items():
        if isinstance(value, re.Pattern):
            if not value.match(md[attr]):
                return False
            continue
        if value is None:
            # attr should not be there
            if attr in md:
                return False
            continue
        if value == '*':
            # attr should be there
            if attr not in md:
                return False
            continue
        if md.get(attr) != attrs[attr]:
            return False
    return True


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--force', action='store_true',
                        help='Re generate data.json form tif files.')
    parser.add_argument('srcdir')
    return parser.parse_args()


def main():
    # TODO: we need a mode to just update as existing json file without parsing
    #       all tiff files. This would be useful to just update titles and
    #       things.
    #       could probably also be done in a separate one off script?
    opts = parse_args()
    opts.srcdir = os.path.abspath(opts.srcdir)

    datajson = os.path.join(opts.srcdir, 'data.json')
    print("Generate data.json")
    if not os.path.exists(datajson) or opts.force:
        print("Rebuild data.json")
        # rebuild data.json
        coverages = []
        # generate all coverages inside source folder
        tiffiles = sorted(glob.glob(os.path.join(opts.srcdir, '**/*.tif'),
                                    recursive=True))
        for tiffile in tqdm.tqdm(tiffiles):
            try:
                md = gen_tif_metadata(tiffile, opts.srcdir, SWIFT_CONTAINER)
                coverage = gen_tif_coverage(tiffile, md['url'])
                md['extent_wgs84'] = get_coverage_extent(coverage)
                md['resolution'] = RESOLUTION
                if md['genre'] == 'DataGenreCC':
                    md['acknowledgement'] = CURRENT_CITATION
                coverage['bccvl:metadata'] = md
                coverage['bccvl:metadata']['uuid'] = gen_coverage_uuid(coverage, 'australia-5km')
                coverages.append(coverage)
            except Exception as e:
                print('Failed to generate metadata for:', tiffile, e)
                raise

        print("Write data.json")
        with open(datajson, 'w') as mdfile:
            json.dump(coverages, mdfile, indent=2)
    else:
        print("Use existing data.json")
        coverages = json.load(open(datajson))

    print("Generate datasets.json")
    datasets = []
    # collect all emscs, gcms, and years from coverages
    GCMS = sorted({cov['bccvl:metadata']['gcm'] for cov in coverages if 'gcm' in cov['bccvl:metadata']})
    EMSCS = sorted({cov['bccvl:metadata']['emsc'] for cov in coverages if 'emsc' in cov['bccvl:metadata']})
    YEARS = sorted({cov['bccvl:metadata']['year'] for cov in coverages if 'emsc' in cov['bccvl:metadata']})
    # generate datasets for db import
    for dsdef in DATASETS:
        # make a copy so that we can modify the filters
        dsdef = copy.deepcopy(dsdef)
        cov_filter = dsdef['filter']
        if cov_filter['genre'] == 'DataGenreCC':
            # current
            subset = list(filter(
                lambda x: match_coverage(x, cov_filter),
                coverages
            ))
            if not subset:
                print("No Data matched for {}".format(cov_filter))
                continue
            coverage = gen_dataset_coverage(subset, dsdef['aggs'])
            md = gen_dataset_metadata(dsdef, subset, genre=cov_filter['genre'])
            md['extent_wgs84'] = get_coverage_extent(coverage)
            coverage['bccvl:metadata'] = md
            coverage['bccvl:metadata']['uuid'] = gen_coverage_uuid(coverage, 'australia-5km')
            datasets.append(coverage)
        else:
            # future
            for gcm, emsc, year in itertools.product(GCMS, EMSCS, YEARS):
                cov_filter.update({
                    'gcm': gcm,
                    'emsc': emsc,
                    'year': year
                })
                subset = list(filter(
                    lambda x: match_coverage(x, cov_filter),
                    coverages
                ))
                if not subset:
                    print("No Data matched for {}".format(cov_filter))
                    continue
                coverage = gen_dataset_coverage(subset, dsdef['aggs'])
                md = gen_dataset_metadata(dsdef, subset, gcm=gcm, emsc=emsc, year=year, genre=cov_filter['genre'])
                md['extent_wgs84'] = get_coverage_extent(coverage)
                coverage['bccvl:metadata'] = md
                coverage['bccvl:metadata']['uuid'] = gen_coverage_uuid(coverage, 'australia-5km')
                datasets.append(coverage)

    print("Write datasets.json")
    # save all the data
    with open(os.path.join(opts.srcdir, 'datasets.json'), 'w') as mdfile:
        json.dump(datasets, mdfile, indent=2)

    print("Write collection.json")
    with open(os.path.join(opts.srcdir, 'collection.json'), 'w') as mdfile:
        # add datasets
        for ds in datasets:
            COLLECTION['datasets'].append({
                "uuid": ds['bccvl:metadata']['uuid'],
                "title": ds['bccvl:metadata']['title']
            })
        json.dump([COLLECTION], mdfile, indent=2)


if __name__ == "__main__":
    main()
