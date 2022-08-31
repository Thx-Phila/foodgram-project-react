import json

import psycopg2

con = psycopg2.connect(
    "dbname=postgres user=postgres password=153794862 host=db")
cur = con.cursor()
insert_sql = """
INSERT INTO recipe_ingredient (name, measurement_unit) VALUES(%s, %s)
"""
with open('data/ingredients.json', 'r', encoding='utf-8') as json_file:
    record_dict = json.load(json_file)
    for record in record_dict:
        cur.execute(insert_sql, [record['name'], record['measurement_unit']])
    con.commit()
