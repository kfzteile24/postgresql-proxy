import psycopg2
import re

# The field to replace
field_pattern = re.compile('(?<=[^\w])count\(distinct (?:cast\()?("[^"]+")\.("[^"]+")(?: as text\))?\)', re.IGNORECASE)
# Table name
table_pattern = re.compile('from \(\s*select \* from ([^\)]+)\s*\) (?:AS )?("[^"]+")', re.IGNORECASE | re.DOTALL)

def rewrite_query(query, context):
    original_table = ''
    table_alias = ''

    # cache only works on current query. Mainly because there's no way to tell if the table has been modified between
    # 2 different requests.
    column_cache = {}

    # Replaces
    # COUNT(DISTINCT CAST("Some Table Alias"."Some Field" AS TEXT))
    # With
    # hll_cardinality(hll_union_agg("Some Table Alias"."Some Field") :: BIGINT
    # Only for "Some Table Alias"."Some Field" that are hll
    def replace(match):
        field_table_alias = match.group(1)
        if field_table_alias.strip('" ') == table_alias.strip('" '):
            hll_table = original_table
            hll_column_candidate = match.group(2).strip()

            # need to know which columns are hll
            if not hll_table.lower() in column_cache:
                db_conn_info = context.instance_config.redirect
                conn = None
                try:
                    conn = psycopg2.connect(
                        "host='{}' port={} dbname='{}' user='{}'".format(
                            # Get host info from proxy config
                            db_conn_info.host,
                            db_conn_info.port,
                            # Get auth information from the proxied request
                            context.connect_params['database'],
                            context.connect_params['user']
                        )
                    )
                    
                    hll_type_code = None
                    cur = conn.cursor()
                    try:
                        cur.execute("SELECT oid FROM pg_type WHERE typname='hll';")
                        hll_type_code, = cur.fetchone()
                    except:
                        pass
                    finally:
                        cur.close()

                    # If there's no hll in the database, no need to replace anything
                    if hll_type_code is None:
                        return match.group(0)

                    # Create a set of all hll columns, and cache it for any other replacement for the same query
                    cur = conn.cursor()
                    try:
                        cur.execute("SELECT * FROM {} LIMIT 0".format(hll_table))
                        hll_columns = set()
                        for desc in cur.description:
                            if desc.type_code == hll_type_code:
                                hll_columns.add(desc.name.lower())

                        column_cache[hll_table.lower()] = hll_columns
                    except:
                        pass
                    finally:
                        cur.close()
                except:
                    raise
                finally:
                    if conn is not None:
                        conn.close()

            # Replace
            if hll_column_candidate.strip('"').lower() in column_cache[hll_table.lower()]:
                return ' hll_cardinality(hll_union_agg({}.{})) :: BIGINT '.format(match.group(1), match.group(2))

        # Don't replace
        return match.group(0)


    query = query.decode('utf-8')
    # Matches this string. The 2 groups are `schema.table` and `"alias"`
    # FROM (SELECT * FROM schema.table) "alias"
    table_result = table_pattern.search(query)
    if table_result is not None:
        original_table = table_result.group(1).strip()
        table_alias = table_result.group(2).strip()

    # Replaces count(distinct ...) with hll_cardinality(hll_union_agg(...)) :: BIGINT
    # where and how it is appropriate
    # the inner function `replace` uses the variables `original_table` and `table_alias` from this scope (smelly code)
    return field_pattern.sub(replace, query).encode('utf-8')
