#!/usr/bin/env python3


import sys
import os
import argparse
import colibricore
import json
import cherrypy
from jinja2 import Environment, FileSystemLoader

SCRIPTDIR = os.path.dirname(os.path.abspath(__file__))
templates = Environment(loader=FileSystemLoader(os.path.join(SCRIPTDIR, 'templates')))

MAXCANDIDATES = 100


class Predictor:
    def __init__(self, patternmodel, corpus, classdecoder, classencoder, title=""):
        self.patternmodel = patternmodel
        self.corpus = corpus
        self.classdecoder = classdecoder
        self.classencoder = classencoder
        self.title = title

    def query(self, leftcontext, filter=""):
        response = {'count':0, 'candidates':[]}

        leftcontext = self.classencoder.buildpattern(leftcontext)

        try:
            incache = self.previouscontext == leftcontext
        except:
            incache = False

        if incache:
            leftcontext = self.previouscontext_found
        else:
            self.previouscontext = leftcontext

        found = False
        while not found:
            if not incache and not leftcontext.unknown():
                found = leftcontext in self.patternmodel
                self.previouscontext_found = leftcontext

            if found or incache:
                found = True #in case we come here through the cache

                #get count
                response['count'] = self.patternmodel.occurrencecount(leftcontext)
                response['context'] = leftcontext.tostring(self.classdecoder)

                #get patterns to the right
                i = 0
                try:
                    for pattern, count in sorted( self.patternmodel.getrightneighbours(leftcontext, args.threshold), key= lambda x: -1 * x[1] ):
                        patternstring = pattern.tostring(self.classdecoder)
                        if i < MAXCANDIDATES and (not filter or patternstring.startswith(filter)):
                            response['candidates'].append( ( patternstring, count ) )
                            i += 1
                except KeyError:
                    pass

                if not response['candidates']:
                    found = False

            if not found:
                #can we shorten the context?
                if len(leftcontext) > 1:
                    #shorten
                    leftcontext = leftcontext[1:]
                else:
                    break

        return response


    @cherrypy.expose
    def predict(self, context, filter=""):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        response = self.query(context, filter)
        response['candidates'] = [ {'text': text, 'count': count} for text, count in response['candidates'] ] #reorganise for json
        return json.dumps(response).encode('utf-8')

    @cherrypy.expose
    def index(self):
        template = templates.get_template('predictor.html')
        return template.render(title=self.title)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Colibri Predictor is a predictive text service using colibri models", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-m','--modelfile', type=str,help="An indexed patternmodel", action='store',required=True)
    parser.add_argument('-d','--datafile',type=str,help="The corpus data file", action='store',required=True)
    parser.add_argument('-c','--classfile',type=str,help="The class file", action='store',required=True)
    parser.add_argument('-t','--threshold',type=int,help="Occurrence threshold (value only has an effect if higher than the threshold with which the model was built)", action='store',default=2,required=False)
    parser.add_argument('-l','--maxlength',type=int,help="Maximum pattern length (value only has an effect if lower than the length with which the model was built)", action='store',default=10,required=False)
    parser.add_argument('-i','--stdin', help="No webserver, read from stdin", action='store_true',default=False,required=False)
    parser.add_argument('-p','--port',type=int, help="Webserver port", action='store',default=8080,required=False)
    parser.add_argument('--title',type=str,help="An extra title to show", action='store',default="",required=False)
    args = parser.parse_args()

    print("Loading class encoder",file=sys.stderr)
    classencoder = colibricore.ClassEncoder(args.classfile)

    print("Loading class decoder",file=sys.stderr)
    classdecoder = colibricore.ClassDecoder(args.classfile)

    print("Loading corpus data",file=sys.stderr)
    corpus = colibricore.IndexedCorpus(args.datafile)

    print("Loading pattern model",file=sys.stderr)
    options = colibricore.PatternModelOptions(mintokens=args.threshold,maxlength=args.maxlength)
    patternmodel = colibricore.IndexedPatternModel(args.modelfile, options, None, corpus)

    if args.stdin:
        predictor = Predictor(patternmodel, corpus, classdecoder, classencoder)
        while True:
            context = input('--> ')
            if '\t' in context:
                context, filter = context.split('\t')
            else:
                filter = ""
            d = predictor.query(context, filter)
            print(d)

    else:
        #sys.argv = [ sys.argv[0] ]
        #webservice = web.application(urls, globals())
        #webservice.run()
        config = {
            'global': {
                'server.socket_host': '0.0.0.0',
                'server.socket_port': args.port,
            },
            '/static': {
                'tools.staticdir.on'            : True,
                'tools.staticdir.dir'           : os.path.join(SCRIPTDIR, 'static'),
                'tools.staticdir.content_types' : {'html': 'application/octet-stream'}
            }
        }
        def fake_wait_for_occupied_port(host, port): return
        cherrypy.process.servers.wait_for_occupied_port = fake_wait_for_occupied_port
        cherrypy.quickstart(Predictor(patternmodel, corpus, classdecoder, classencoder, args.title), config=config)

