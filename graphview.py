#!/usr/bin/env python3

from __future__ import print_function, unicode_literals, division, absolute_import
import argparse
import cherrypy
import colibricore
import sys
import os

SCRIPTDIR = os.path.dirname(os.path.abspath(__file__))

def safe(s):
    return s.replace("'","`")


def processrelations(type, func,  pattern, threshold, nodes, edges, classdecoder, colors, relationtypes="",secondorderedges=False):
    if not relationtypes or type in relationtypes:
        for pattern2, count in func(pattern):
            nodeid= safe(type + pattern2.tostring(classdecoder))
            if not nodeid in nodes:
                nodes[nodeid] =  [nodeid, pattern2, count,type]
            edges.append( [nodeid, pattern, pattern2, type, count] )

    tmpnodeset = set()
    for nodeid,p,_,_ in nodes.values():
        if nodeid[0] == type:
            tmpnodeset.add(p)

    if secondorderedges:
        for p in tmpnodeset:
            if p != pattern:
                try:
                    for p2, count in func(p, threshold):
                        if p2 in tmpnodeset and p2 != pattern:
                            nodeid= safe(type + p2.tostring(classdecoder))
                            if not nodeid in nodes:
                                nodes[nodeid] =  [nodeid, p2, count,type]
                            edges.append( [nodeid, p, p2, type, count] )
                except KeyError:
                    continue

class Root:
    def __init__(self, patternmodel, classdecoder, classencoder, threshold):
        self.patternmodel = patternmodel
        self.classdecoder = classdecoder
        self.classencoder = classencoder
        self.threshold = threshold

    @cherrypy.expose
    def query(self, pattern, relationtypes="", threshold=0):
        if threshold == 0:
            threshold = self.threshold
        pattern = self.classencoder.buildpattern(pattern)
        if pattern in self.patternmodel:


            nodes = {}
            nodes['center'] = ['center', pattern, self.patternmodel.occurrencecount(pattern),'center' ]
            edges = []

            minnodesize = 1
            maxnodesize = 10
            minedgesize = 1
            maxedgesize = 10

            colors = {'center':'#ff0000', 'c': "#222" , 'p': "#222",'r': "#32883c" ,'l': "#32883c",'t': '#323288','R':'#2e7469','L':'#2e7469' }
            extra = {'c': "arrow: 'target'",'p':"arrow: 'source'", 'l':  "arrow: 'source'" ,'r':  "arrow: 'target'", 'L':  "arrow: 'source'" ,'R':  "arrow: 'target'", 't': "arrow: 'source'"}

            processrelations('c',self.patternmodel.getsubchildren, pattern, threshold, nodes, edges, self.classdecoder, colors, relationtypes,True)
            processrelations('p',self.patternmodel.getsubparents, pattern,  threshold, nodes, edges, self.classdecoder,  colors,relationtypes,True)
            processrelations('l',self.patternmodel.getleftneighbours, pattern,  threshold,nodes, edges, self.classdecoder,  colors,relationtypes)
            processrelations('r',self.patternmodel.getrightneighbours, pattern,  threshold,nodes, edges,self.classdecoder,  colors,relationtypes)
            processrelations('t',self.patternmodel.gettemplates, pattern,  threshold, nodes, edges,self.classdecoder,  colors,relationtypes,True)
            #processrelations('L',self.patternmodel.getleftcooc, pattern, nodes, edges, self.classdecoder,  colors,relationtypes)
            #processrelations('R',self.patternmodel.getrightcooc, pattern, nodes, edges,self.classdecoder,  colors,relationtypes)

            jscode = """
var i,
s,
N = 100,
E = 500,
g = {
    nodes: [],
    edges: []
};"""


            #jscode = " var sigRoot = document.getElementById('graph');\n sigInst = sigma(sigRoot);"
            #jscode += " sigInst.drawingProperties({ defaultLabelColor: '#222', defaultLabelSize: 14, defaultLabelHoverColor: '#000', labelThreshold: 6, font: 'Arial', edgeColor: 'source', defaultEdgeType: 'curve' });\n"
            #jscode += " sigInst.graphProperties({ minNodeSize: " + str(minnodesize) + ", maxNodeSize: " + str(maxnodesize) + ", minEdgeSize: " + str(minedgesize) + ", maxEdgeSize: " + str(maxedgesize) + " });\n"
            #jscode += " sigInst.mouseProperties({ maxRatio: 450, minRatio: .1, marginRatio: 1, zoomDelta: 0.1, dragDelta: 0.3, zoomMultiply: 1.5, inertia: 1.1 });\n"
            #jscode += " sigInst.bind('upnodes', function(event){  var q = event.content[0].substr(1); window.location.assign('/query/?pattern=' + q );});\n"


            for nodeid, p, count, type in nodes.values():
                s = safe(p.tostring(self.classdecoder))
                size = count
                color = colors[type]

                jscode += " g.nodes.push({id:'" +  nodeid + "',text: '" + safe(s) + "', label: '" + s + " (" + str(count) + ")', 'size':"+str(size)+",'cluster': '" + type + "', 'color': '" + color + "', 'x': Math.random(),'y': Math.random() });\n"

            for nodeid, frompattern,topattern, type, count in edges:
                if frompattern == pattern:
                    s_from = 'center'
                else:
                    s_from = safe(type + frompattern.tostring(self.classdecoder))
                s_to = nodeid
                s_edgeid = s_from + "_REL" + type + "_" + s_to
                color = colors[type]
                if type in extra:
                    e = ", " + extra[type]
                else:
                    e = ""
                size = count
                jscode += " g.edges.push({id: '" + s_edgeid + "', source: '" +s_from  + "', target: '" +s_to  + "' ,size:" + str(size) + ", 'color':'" + color + "'" + e + "});\n"

            jscode += "s = new sigma({graph: g, container: 'graph'});"
            jscode += "s.startForceAtlas2({startingIterations: 5, iterationsPerRender: 5});\n"
            jscode += "s.bind('clickNode', function(e) { var q = e.data.node.text.replace('`',\"'\"); window.location.assign('../query/?pattern=' + q );});\n"
            jscode += "window.setTimeout(function(){ s.stopForceAtlas2();}, 10000);\n";
            jscode = "$(document).ready(function(){\n" + jscode + "\n});"
        else:
            jscode = ""

        return self.page("../",jscode)

    @cherrypy.expose
    def index(self):
        return self.page()

    def page(self, prefix="",jscode=""):
        html = "<html><head><title>Colibri PatternGraphView</title>"
        html += "<meta charset=\"utf-8\">"
        html += "<script src=\"" + prefix + "static/jquery-2.1.1.min.js\"></script>"
        html += "<script src=\"" + prefix + "static/sigma.min.js\"></script>"
        html += "<script src=\"" + prefix + "static/sigma.layout.forceAtlas2/worker.js\"></script>"
        html += "<script src=\"" + prefix + "static/sigma.layout.forceAtlas2/supervisor.js\"></script>"
        html += "<script type=\"text/javascript\">" + jscode + "</script>"
        html += "<link rel=\"stylesheet\" href=\"" + prefix + "static/predictor.css\" type=\"text/css\" media=\"all\" />"
        html += "</head>"
        html += '<body><div id="container"><div id="header"> <div id="lamalogo"></div> <div id="rulogo"></div> <h1>Colibri Graph Viewer</h1> </div>'
        if jscode:
            html += "<div id=\"graph\" style=\"width: 90%; height:90%; \"></div>"
        else:
            html += "<div id=\"graph\"></div><div class=\"box\">"
            html += "<p>Pattern not found</p>"
        html += "<form action=\"" + prefix + "query/\" method=\"post\"><input name=\"pattern\" /><input type=\"submit\"></form></div>"
        return html



def main():
    parser = argparse.ArgumentParser(description="Colibri Graph View - Visualises a pattern model", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-m','--modelfile', type=str,help="The Indexed Pattern Model to load", action='store',required=True)
    parser.add_argument('-c','--classfile', type=str,help="The class file", action='store',required=True)
    parser.add_argument('-p','--port', type=int,help="Port", action='store',default=8080,required=False)
    parser.add_argument('-t','--threshold', type=int,help="Threshold, consider only related patterns occuring at least this many times", action='store',default=2,required=False)
    args = parser.parse_args()

    print("Loading class encoder",file=sys.stderr)
    classencoder = colibricore.ClassEncoder(args.classfile)
    print("Loading class decoder",file=sys.stderr)
    classdecoder = colibricore.ClassDecoder(args.classfile)
    print("Loading pattern model",file=sys.stderr)
    patternmodel = colibricore.IndexedPatternModel(args.modelfile)

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
    cherrypy.quickstart(Root(patternmodel, classdecoder, classencoder, args.threshold), config=config)

if __name__ == '__main__':
    main()
