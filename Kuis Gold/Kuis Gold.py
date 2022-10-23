
from ast import Delete, In
from os import remove
from tkinter import S
from flask import Flask, request, jsonify
from flasgger import Swagger, LazyString, LazyJSONEncoder, swag_from
import re
import pandas as pd
import sqlite3

app = Flask(__name__)

app.json_encoder = LazyJSONEncoder


swagger_template = dict(
    info = {
        'title': LazyString(lambda:'API Documentation for Data Cleansing'),
        'version': LazyString(lambda:'1.0.0'),
        'description': LazyString(lambda:'API Documentation for Data Cleansing')
        }, host = LazyString(lambda: request.host)
    )

swagger_config = {
        "headers":[],
        "specs":[
            {
            "endpoint":'docs',
            "route":'/docs.json'
            }
        ],
        "static_url_path":"/flasgger_static",
        "swagger_ui":True,
        "specs_route":"/docs/"
    }

swagger = Swagger(app, template=swagger_template, config=swagger_config)

def lowercase(s):
    return s.lower() #mengubah karakter menjadi lowercase

def remove_punct(s):
    s = re.sub(r'\n',' ',s) #
    s = re.sub('user',' ', s) #
    s = re.sub('rt',' ', s) #
    s = re.sub('((www\.[^\s]+)|(https?://[^\s]+)|(http?://[^\s]+))',' ',s ) #
    s = re.sub(r'[^\w\d\s]+', ' ',s) #
    s = re.sub(r' +',' ',s) #
    s = re.sub(r'[^0-9a-zA-Z]+',' ',s) #

    return s 


db = sqlite3.connect('/Users/mohammadraditya/Kuis Gold/gabungan.db' ,  check_same_thread=False)
q_kamus_alay= 'select * from kamus_alay'
t_kamus_alay=  pd.read_sql_query(q_kamus_alay, db)
q_abusive = 'select * from abusive'
t_abusive = pd.read_sql_query(q_abusive, db)

alay_dict_map = dict(zip(t_kamus_alay['anakjakartaasikasik'],t_kamus_alay['anak jakarta asyik asyik']))
def normalize_alay(s):
    for word in alay_dict_map:
        return ' '.join([alay_dict_map[word] if word in alay_dict_map else word for word in s.split(' ')])

p_abusive = t_abusive['ABUSIVE'].str.lower().tolist()
def normalize_abusive (s):
    word_list = s.split()
    return ' '.join([s for s in word_list if s not in p_abusive ])


def cleansing (s):
    s = lowercase(s)
    s = remove_punct(s)
    s = normalize_alay(s)
    s = normalize_abusive(s)
    return s

@swag_from("docs/input_data.yml", methods=['POST'])
@app.route('/input_data', methods=['POST'])
def test ():
    input_text = str(request.form["input_data"])
    output_text = cleansing(input_text)

    db.execute('create table if not exists input_data (input_text varchar(255), output_text varchar(255))')
    query_text = 'insert into input_data (input_text , output_text) values (?,?)'
    val = (input_text,output_text)
    db.execute(query_text,val)
    db.commit()

    return_text = { "input" :input_text, "output" : output_text}
    return jsonify (return_text)

@swag_from("docs/upload_data.yml", methods=['POST'])
@app.route('/upload_data', methods=['POST'])
def upload_file():
    file = request.files["upload_data"]
    df_csv = (pd.read_csv(file, encoding="latin-1"))

    df_csv['new_tweet'] = df_csv['Tweet'].apply(cleansing)
    df_csv.to_sql("clean_tweet", con=db, index=False, if_exists='append')
    db.close()

    cleansing_tweet = df_csv.new_tweet.to_list()

    return_file = {
        'output' : cleansing_tweet}
    return jsonify(return_file)



if __name__ == '__main__':
	app.run(debug=True, port=8080)
