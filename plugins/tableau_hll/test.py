import collections
import os
import plugins.tableau_hll as hll
import yaml

class TestContext():
    def __init__(self):
        with open(os.path.dirname(__file__) + '/config.yml', 'r') as fp:
            self.config = yaml.load(fp)
        InstanceConfig = collections.namedtuple('InstanceConfig', 'redirect')
        Redirect = collections.namedtuple('Redirect', 'name host port')
        self.instance_config = InstanceConfig(redirect=Redirect(**self.config['redirect']))
        self.connect_params = self.config['connect_params']


def run():
    query = b'SELECT COUNT(DISTINCT "crm_data_source"."Set of Customers") AS "ctd:Set of Customers:ok"\nFROM "crm_dim"."crm_data_source" "crm_data_source"\nHAVING (COUNT(1) > 0);'
    out_query = b'SELECT  hll_cardinality(hll_union_agg("crm_data_source"."Set of Customers")) :: BIGINT  AS "ctd:Set of Customers:ok"\nFROM "crm_dim"."crm_data_source" "crm_data_source"\nHAVING (COUNT(1) > 0);'
    context = TestContext()
    assert hll.rewrite_query(query, context) == out_query
