#!/usr/bin/env python
import os.path
import calendar

from data_conversion.converter import BaseLayerMetadata
from data_conversion.vocabs import RESOLUTIONS, collection_by_id
from data_conversion.utils import FilterType


class ANUClimLayerMetadata(BaseLayerMetadata):

    DATASET_ID = 'anuclim'
    SWIFT_CONTAINER = (
        'https://swift.rc.nectar.org.au/v1/AUTH_0bc40c2c2ff94a0b9404e6f960ae5677/'
        'anuclim_layers'
    )

    DATASETS = [
        # current
        {
            # bio
            'title': 'ANUClim (Australia), Current Climate {monthname}, (1976-2005), {resolution}',
            'description': (
                'Monthly climate data for the Australian continent between 1976-2005, '
                'generated using ANUClimate 1.0. This dataset includes 5 variables: '
                'monthly total precipitation, mean daily minimum and maximum temperature '
                'of the month, mean daily vapour pressure of the month and monthly total '
                'class A pan evaporation. The monthly anomalies were interpolated by '
                'trivariate thin plate smoothing spline functions of longitude, latitude '
                'and vertically exaggerated elevation using ANUSPLIN Version 4.5. Monthly '
                'data values were calculated from Bureau of Meteorology daily data at '
                'stations where there were no missing observations and any accumulated '
                'records were wholly within the month.'
            ),
            'categories': ['environmental', 'climate'],
            'domain': 'terrestrial',
            'spatial_domain': 'Australia',
            'acknowledgement': (
                'Hutchinson M, Kesteven J, Xu T (2014) Monthly climate data: ANUClimate 1.0, '
                '0.01 degree, Australian Coverage, 1976-2005. Australian National University, '
                'Canberra, Australia. Made available by the Ecosystem Modelling and Scaling '
                'Infrastructure (eMAST, http://www.emast.org.au) of the Terrestrial Ecosystem '
                'Research Network (TERN, http://www.tern.org.au).'
            ),
            'external_url': 'https://researchdata.ands.org.au/anuclimate-collection/983248',
            'license': (
                'Creative Commons Attribution 4.0'
                'https://creativecommons.org/licenses/by/4.0/'
            ),
            'partof': [collection_by_id('anuclim_layers')['uuid']],
            'filter': {
                'time_domain': 'Current',
                'month': FilterType.DISCRIMINATOR
            },
            'aggs': [], 
        }
    ]

    def parse_filename(self, tiffile):
        return {
            'resolution': RESOLUTIONS['30']['long'],
            'spatial_domain': 'Australia',
        }

    def gen_dataset_metadata(self, dsdef, coverages):
        ds_md = {
            'categories': dsdef['categories'],
            'domain': dsdef['domain'],
            'spatial_domain': dsdef['spatial_domain'],
            'time_domain': dsdef['filter']['time_domain'],
            'resolution': RESOLUTIONS['30']['long'],
            'acknowledgement': dsdef.get('acknowledgment'),
            'external_url': dsdef.get('external_url'),
            'license': dsdef.get('license'),
            'title': dsdef['title'].format(
                resolution=RESOLUTIONS['30']['long'],
                monthname=calendar.month_name[int(dsdef['filter']['month'])],
                **dsdef['filter']
            ),
            'month': dsdef['filter']['month']
        }
        # all coverages have the same year and year_range
        ds_md['year'] = coverages[0]['bccvl:metadata']['year']
        ds_md['year_range'] = coverages[0]['bccvl:metadata']['year_range']
        return ds_md


def main():
    gen = ANUClimLayerMetadata()
    gen.main()

    
if __name__ == "__main__":
    main()
