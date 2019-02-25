import collections
import os
import plugins.tableau_hll as hll
import yaml

def test_context():
    with open(os.path.dirname(__file__) + '/config.yml', 'r') as fp:
        config = yaml.load(fp)
    InstanceConfig = collections.namedtuple('InstanceConfig', 'redirect')
    Redirect = collections.namedtuple('Redirect', 'name host port')
    return {
        'instance_config': InstanceConfig(redirect=Redirect(**config['redirect'])),
        'connect_params': config['connect_params']
    }


def run():
    queries = [
        (
            'SELECT COUNT(DISTINCT "crm_data_source"."Set of Customers") AS "ctd:Set of Customers:ok"\nFROM "crm_dim"."crm_data_source" "crm_data_source"\nHAVING (COUNT(1) > 0);',
            'SELECT  hll_cardinality(hll_union_agg("crm_data_source"."Set of Customers")) :: BIGINT  AS "ctd:Set of Customers:ok"\nFROM "crm_dim"."crm_data_source" "crm_data_source"\nHAVING (COUNT(1) > 0);'
        ),
        (
            'BEGIN;declare "SQL_CUR0x7fb46c01e3b0" cursor with hold for SELECT CAST("crm_data_source"."Campaign Name" AS TEXT) AS "Campaign Name",\n  COUNT(DISTINCT "crm_data_source"."Set of Unique Clicks") AS "usr:# Unique Customers (copy):ok"\nFROM "crm_dim"."crm_data_source" "crm_data_source"\nGROUP BY 1;fetch 2048 in "SQL_CUR0x7fb46c01e3b0"',
            'BEGIN;declare "SQL_CUR0x7fb46c01e3b0" cursor with hold for SELECT CAST("crm_data_source"."Campaign Name" AS TEXT) AS "Campaign Name",\n   hll_cardinality(hll_union_agg("crm_data_source"."Set of Unique Clicks")) :: BIGINT  AS "usr:# Unique Customers (copy):ok"\nFROM "crm_dim"."crm_data_source" "crm_data_source"\nGROUP BY 1;fetch 2048 in "SQL_CUR0x7fb46c01e3b0"'
        )
    ]
    context = test_context()
    for src, dst in queries:
        res = hll.rewrite_query(src, context)
        try:
            assert res == dst
        except AssertionError:
            print(f"Rewriting query:\n\n{src}\n\nExpecting:\n\n{dst}\n\nGot:\n\n{res}")
