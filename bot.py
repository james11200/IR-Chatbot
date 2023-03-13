import json
from flask import Flask, request, Response
from transformers import pipeline, Conversation
from elasticsearch import Elasticsearch
from flask_cors import CORS, cross_origin
from elasticsearch import Elasticsearch
import sys

# init elasticsearch
es = Elasticsearch("https://34.130.142.208:9200", basic_auth=("elastic",  "G3Ir7gAO3wwx1MkfnIBA"), verify_certs=False)
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
# flask init
app = Flask(__name__)
CORS(app)

@app.route('/bot/', methods=['POST'])
@cross_origin()
def bot():
    """Pipeline for using our bot"""
    # format request into elastic search query of type (TEXT AND (SUBJ1 OR SUBJ2 OR...))
    client_request = request.json
    print(client_request['user_utterances'])
    print(client_request['bot_utterances'])
    if client_request['bot_utterances']:
        to_classify = [client_request['bot_utterances'][-1], client_request['user_utterances'][-1] ]
    else:
        to_classify = [client_request['user_utterances'][-1]]
    pos_labels = ['chitchat', 'politics', 'environment', 'technology', 'healthcare', 'education']
    labels = classifier(" ".join(to_classify), pos_labels, multi_labels=True)
    print(labels, file=sys.stderr)
    if client_request['context'] == '':
        if labels['labels'][0] == 'smalltalk' or labels['labels'][0] == 'chitchat':
            return _chitchat_query(client_request)
        else:
            return _contextless_query(client_request)
    else:
        if labels['labels'][0] == 'smalltalk' or labels['labels'][0] == 'chitchat':
            return _chitchat_query(client_request)
        else:
            return  _context_query(client_request)


def _context_query(client_request):
    query = {
        "bool" : {
            "must": [
                {
                    "wildcard" : {
                        "parent_id" : {"value" : f"*_{client_request['context']}"}
                    }
                },
                {
                    "match" : {"body" : client_request['query']}
                }
            ]
        }
    }


    # search comments of first post
    result = es.search(index="comment_index", query=query)
    # they probably changed the subject
    if result['hits']['max_score'] is None:
        print('contextless')
        return _contextless_query(client_request)

    else:
        return json.dumps({"response": result['hits']['hits'][0]['_source']['body']
        , "post" :  client_request['context']})
def _chitchat_query(client_requests):
    context_list = []
    for i, human in enumerate(client_requests['user_utterances'][:len(client_requests['user_utterances']) - 1]):
        context_list.append(human)
        context_list.append(client_requests['bot_utterances'][i])
    context = " ".join(context_list)
    context = context[len(context) - 3:]
    resp = es.search(index="chitchat", query={"dis_max": {'queries':[{ "match": {"current_state^2": {'query': context, 'fuzziness' : 'AUTO'} }},
                                              {"match": {"last_utterance" :{"query": client_requests['query'], 'fuzziness': "AUTO"}}}
], "tie_breaker": 0.1}})
    if resp['hits']['hits']:
        return json.dumps({'response': resp['hits']['hits'][0]['_source']['resp'], 'post': "" })
    else:
        return json.dumps({'response': "I do not understand", 'post': "" })

def _contextless_query(client_request):
    query = {
        "bool" : {
            "must": [
                {
                    "multi_match" : {
                        "query" : client_request['query'],
                        "fields" : ["selftext", "title"]
                }
            },
            {"bool": {"should" :[]}}
            ],
        }
    }
    for topic in client_request["topics"]:
       query["bool"]["must"][1]['bool']['should'].append({"match" :{ "topic" : topic}})

    result = es.search(index="reddit_index", query=query)

    if result['hits']['max_score'] is None:
        return json.dumps({"response" : "I don't know what you mean by that", 'post' : ''})

    post = result['hits']['hits'][0]['_source']['id']
    print(post)
    print(result)

    
    return json.dumps({"response": result['hits']['hits'][0]['_source']['selftext']
    , "post" :  post})
    

    # query = {
    #     "bool" : {
    #         "must": [
    #             {
    #                 "wildcard" : {
    #                     "parent_id" : {"value" : f"*_{post}"}
    #                 }
    #             },
    #             {
    #                 "match" : {"body" : client_request['query']}
    #             }
    #         ]
    #     }
    # }

    # result = es.search(index="comment_index", query=query)
    # print(result)

    # # if you have no results
    # if result['hits']['max_score'] is None:
    #     return json.dumps({"response" : "I don't know what you mean by that", 'post' : ''})

    # # if you have results
    # return json.dumps({"response": result['hits']['hits'][0]['_source']['body']
    # , "post" :  result['hits']['hits'][0]['_source']['id']})


app.run()