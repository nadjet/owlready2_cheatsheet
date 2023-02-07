# Owlready2
# Copyright (C) 2021 Jean-Baptiste LAMY
# LIMICS (Laboratoire d'informatique médicale et d'ingénierie des connaissances en santé), UMR_S 1142
# University Paris 13, Sorbonne paris-Cité, Bobigny, France

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from owlready2.sparql.main import PreparedSelectQuery


_mime_2_format = {
    "text/xml"                        : "execute_xml",
    "application/sparql-results+xml"  : "execute_xml",
    "application/rdf+xml"             : "execute_xml",
    "text/json"                       : "execute_json",
    "application/json"                : "execute_json",
    "application/sparql-results+json" : "execute_json",
    "text/csv"                        : "execute_csv",
    "text/tab-separated-values"       : "execute_tsv",
}

class EndPoint(object):
  def __init__(self, world, read_only = True, no_cache = False):
    self.world     = world
    self.read_only = read_only
    self.no_cache  = no_cache
    self.__name__  = "endpoint%s" % id(self)
    
  def __call__(self):
    import flask
    query  = flask.request.args.get("query", "")
    mime   = flask.request.headers.get("Accept", "text/csv")
    format = _mime_2_format.get(mime)
    if format is None:
      mime   = "text/csv"
      format = "execute_csv"
      
    q = self.world.prepare_sparql(query)
    if self.read_only and not isinstance(q, PreparedSelectQuery): return ""
    
    r = flask.Response( getattr(q, format)() , mimetype = mime)
    if self.no_cache: r.cache_control.no_cache = True
    return r
  
  def wsgi_app(self, environ, start_response):
    import urllib.parse
    args   = urllib.parse.parse_qs(environ["QUERY_STRING"])
    query  = args.get("query")[0]
    mime   = environ.get("HTTP_ACCEPT", "text/csv")
    format = _mime_2_format.get(mime)
    if format is None:
      mime   = "text/csv"
      format = "execute_csv"
      
    q = self.world.prepare_sparql(query)
    if self.read_only and not isinstance(q, PreparedSelectQuery): return ""
    
    headers = [("Content-type", "%s; charset=utf-8" % mime)]
    if self.no_cache: headers.append(("Cache-Control", "no-cache"))
    start_response("200 OK", headers)
    
    return [ getattr(q, format)().encode("utf-8") ]
    
