#!/usr/bin/env python
import os.path

from data_conversion.converter import BaseLayerMetadata
from data_conversion.vocabs import RESOLUTIONS, collection_by_id


class TASClimLayerMetadata(BaseLayerMetadata):

    CATEGORIES = ['environmental', 'climate']
    DATASET_ID = 'tasclim'
    SWIFT_CONTAINER = (
        'https://swift.rc.nectar.org.au/v1/AUTH_0bc40c2c2ff94a0b9404e6f960ae5677/'
        'tasclim_layers'
    )

    DATASETS = [
        # current
        {
            # bio
            'title': 'Tasmania, Current Climate ({year}), ({emsc}) based on {gcm}, {resolution}',
            'acknowledgement': (
                'Corney, S. P., J. J. Katzfey, J. L. McGregor, M. R. Grose, J. C. Bennett, '
                'C. J. White, G. K. Holz, S. Gaynor, and N. L. Bindoff, 2010: Climate '
                'Futures for Tasmania: climate modelling. Antarctic Climate and Ecosystems '
                'Cooperative Research Centre, Hobart, Tasmania.'
            ),
            'external_url': 'http://www.dpac.tas.gov.au/__data/assets/pdf_file/0016/151126/CFT_-_Climate_Modelling_Summary.pdf',
            'license': (
                'Creative Commons Attribution 3.0 AU'
                'https://creativecommons.org/licenses/by/3.0/au'
            ),
            'partof': [collection_by_id('tasclim_layers')['uuid']],
            'filter': {
                'genre': 'DataGenreCC',
                'gcm': None,
                'emsc': None,
                'year': None
            },
            'aggs': [], 
        },
        {
            # bio
            'title': 'Tasmania, Future Climate ({year}), ({emsc}) based on {gcm}, {resolution}',
            'acknowledgement': (
                'Corney, S. P., J. J. Katzfey, J. L. McGregor, M. R. Grose, J. C. Bennett, '
                'C. J. White, G. K. Holz, S. Gaynor, and N. L. Bindoff, 2010: Climate '
                'Futures for Tasmania: climate modelling. Antarctic Climate and Ecosystems '
                'Cooperative Research Centre, Hobart, Tasmania.'
            ),
            'external_url': 'http://www.dpac.tas.gov.au/__data/assets/pdf_file/0016/151126/CFT_-_Climate_Modelling_Summary.pdf',
            'license': (
                'Creative Commons Attribution 3.0 AU'
                'https://creativecommons.org/licenses/by/3.0/au'
            ),
            'partof': [collection_by_id('tasclim_layers')['uuid']],
            'filter': {
                'genre': 'DataGenreFC',
                'gcm': None,
                'emsc': None,
                'year': None
            },
            'aggs': [], 
        }    
    ]

    def parse_filename(self, tiffile):
        return {
            'resolution': RESOLUTIONS['360']['long'],
        }

    def gen_dataset_metadata(self, dsdef, coverages):
        ds_md = {
            'category': self.CATEGORY,
            'genre': dsdef['filter']['genre'],
            'resolution': RESOLUTIONS['360']['long'],
            'acknowledgement': dsdef.get('acknowledgment'),
            'external_url': dsdef.get('external_url'),
            'license': dsdef.get('license'),
            'title': dsdef['title'].format(
                resolution=RESOLUTIONS['360']['long'],
                **dsdef['filter']
            )
        }
        # all coverages have the same year and year_range
        ds_md['year'] = coverages[0]['bccvl:metadata']['year']
        ds_md['year_range'] = coverages[0]['bccvl:metadata']['year_range']

        if dsdef['filter'].get('emsc'):
            ds_md['emsc'] = dsdef['filter']['emsc']
        if dsdef['filter'].get('gcm'):
            ds_md['gcm'] = dsdef['filter']['gcm']
        return ds_md

    def get_genre(self, md):
        if md['year'] < 2016:
            return 'DataGenrceCC'
        return 'DataGenreFC'


def main():
    gen = TASClimLayerMetadata()
    gen.main()


if __name__ == "__main__":
    main()
