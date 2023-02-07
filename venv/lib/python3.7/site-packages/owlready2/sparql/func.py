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


import sys, os, re, urllib.parse, functools, datetime
from owlready2.base import _universal_datatype_2_abbrev, _parse_datetime, rdf_type, owl_named_individual
import owlready2, owlready2.rply as rply


_BOOL_EXPRESSION_MEMBERS   = { "||", "&&", "=", "COMPARATOR", "LIST_COMPARATOR", "BOOL" }
_NUMBER_EXPRESSION_MEMBERS = { "*", "/", "+", "-" }
_FUNC_2_DATATYPE = {
  "STR" : _universal_datatype_2_abbrev[str], # ok
  "LANG" : _universal_datatype_2_abbrev[str], # ok
  "LANGMATCHES" : _universal_datatype_2_abbrev[bool], # ok
  "DATATYPE" : None, # => objs # ok
  "BOUND" : _universal_datatype_2_abbrev[bool], # ok
  "IRI" : None, # ok
  "URI" : None, # ok
  "BNODE" : None, # ok
  "RAND" : _universal_datatype_2_abbrev[float], # ok
  #"ABS" :  # ok
  "CEIL" : _universal_datatype_2_abbrev[float], # ok
  "FLOOR" : _universal_datatype_2_abbrev[float], # ok
  "ROUND" : _universal_datatype_2_abbrev[int], # ok
  #"CONCAT" :  # ok
  "STRLEN" : _universal_datatype_2_abbrev[int], # ok
  #"UCASE" :  # ok
  #"LCASE" :  # ok
  "ENCODE_FOR_URI" : _universal_datatype_2_abbrev[str], # ok
  "CONTAINS" : _universal_datatype_2_abbrev[bool], # ok
  "STRSTARTS" : _universal_datatype_2_abbrev[bool], # ok
  "STRENDS" : _universal_datatype_2_abbrev[bool], # ok
  #"STRBEFORE" :  # ok
  #"STRAFTER" :  # ok
  "YEAR" : _universal_datatype_2_abbrev[int], # ok
  "MONTH" : _universal_datatype_2_abbrev[int], # ok
  "DAY" : _universal_datatype_2_abbrev[int], # ok
  "HOURS" : _universal_datatype_2_abbrev[int], # ok
  "MINUTES" : _universal_datatype_2_abbrev[int], # ok
  "SECONDS" : _universal_datatype_2_abbrev[float], # ok
  "TIMEZONE" : _universal_datatype_2_abbrev[str], # ok
  "TZ" : _universal_datatype_2_abbrev[str], # ok
  "NOW" : _universal_datatype_2_abbrev[datetime.datetime], # ok
  "UUID" : None, # ok
  "STRUUID" : _universal_datatype_2_abbrev[str], # ok
  "MD5" : _universal_datatype_2_abbrev[str], # ok
  "SHA1" : _universal_datatype_2_abbrev[str], # ok
  "SHA256" : _universal_datatype_2_abbrev[str], # ok
  "SHA384" : _universal_datatype_2_abbrev[str], # ok
  "SHA512" : _universal_datatype_2_abbrev[str], # ok
  #"COALESCE" :  # ok
  #"IF" :  # ok
  #"STRLANG" :  # ok
  #"STRDT" :  # ok
  "SAMETERM" : _universal_datatype_2_abbrev[bool], # ok
  "ISIRI" : _universal_datatype_2_abbrev[bool], # ok
  "ISURI" : _universal_datatype_2_abbrev[bool], # ok
  "ISBLANK" : _universal_datatype_2_abbrev[bool], # ok
  "ISLITERAL" : _universal_datatype_2_abbrev[bool], # ok
  "ISNUMERIC" : _universal_datatype_2_abbrev[bool], # ok
  "REGEX" : _universal_datatype_2_abbrev[bool],
  #"SUBSTR" :  # ok
  #"REPLACE" :  # ok
  #"SIMPLEREPLACE" :  # ok
  "NEWINSTANCEIRI" : None, # ok
  "LOADED" : _universal_datatype_2_abbrev[bool], # ok
  "STORID" : _universal_datatype_2_abbrev[int], # ok
  "DATE"    : _universal_datatype_2_abbrev[datetime.date], # ok
  "TIME"    : _universal_datatype_2_abbrev[datetime.time], # ok
  "DATETIME": _universal_datatype_2_abbrev[datetime.datetime], # ok
  "DATE_DIFF": _universal_datatype_2_abbrev[datetime.timedelta], # ok
  "DATE_ADD": _universal_datatype_2_abbrev[datetime.date], # ok
  "DATE_SUB": _universal_datatype_2_abbrev[datetime.date], # ok
  "DATETIME_DIFF": _universal_datatype_2_abbrev[datetime.timedelta], # ok
  "DATETIME_ADD": _universal_datatype_2_abbrev[datetime.datetime], # ok
  "DATETIME_SUB": _universal_datatype_2_abbrev[datetime.datetime], # ok

  "HTTP://WWW.W3.ORG/2001/XMLSCHEMA#INTEGER" : _universal_datatype_2_abbrev[int], # ok
  "HTTP://WWW.W3.ORG/2001/XMLSCHEMA#DOUBLE" : _universal_datatype_2_abbrev[float], # ok
  
  "COUNT" : _universal_datatype_2_abbrev[int], # ok
  "MIN" : 0, # ok
  "MAX" : 0, # ok
  "AVG" : 0, # ok
  "SUM" : 0, # ok
  #"SAMPLE" : 0, # ok
  "GROUP_CONCAT" : _universal_datatype_2_abbrev[str], # ok
  }


import hashlib, uuid
def _md5    (x): return hashlib.md5   (x.encode("utf8")).hexdigest()
def _sha1   (x): return hashlib.sha1  (x.encode("utf8")).hexdigest()
def _sha256 (x): return hashlib.sha256(x.encode("utf8")).hexdigest()
def _sha384 (x): return hashlib.sha384(x.encode("utf8")).hexdigest()
def _sha512 (x): return hashlib.sha512(x.encode("utf8")).hexdigest()
def _struuid():  return str(uuid.uuid4())
def _uuid   ():
  from owlready2.sparql.parser import CURRENT_TRANSLATOR
  CURRENT_TRANSLATOR.get().world
  return CURRENT_TRANSLATOR.get().world._abbreviate("urn:uuid:%s" % str(uuid.uuid4()))

def _seconds(x):
  try: d = _parse_datetime(x)
  except ValueError: return 0.0
  return d.second + d.microsecond / 1000000.0

def _tz(x):
  try: d = _parse_datetime(x)
  except ValueError: return ""
  z = d.tzinfo.tzname(d)
  if z.startswith("UTC"): z = z[3:]
  return z


@functools.lru_cache(maxsize=128)
def _get_regexp(pattern, flags):
  f = 0
  for i in flags:
    if   i == "i": f |= re.IGNORECASE
    elif i == "s": f |= re.DOTALL
    elif i == "m": f |= re.MULTILINE
  return re.compile(pattern, f)

def _regex(s, pattern, flags):
  pattern = _get_regexp(pattern, flags)
  return bool(pattern.search(s))

_REGEX_SUB_ARG_RE = re.compile("\\$([0-9]*)")
def _sparql_replace(s, pattern, replacement, flags):
  pattern = _get_regexp(pattern, flags)
  replacement = _REGEX_SUB_ARG_RE.sub(r"\\\1", replacement)
  return pattern.sub(replacement, s)
  
def _timezone(x):
  delta = _parse_datetime(x).utcoffset()
  if delta.days < 0:
    seconds = -24 * 60 * 60 * delta.days - delta.seconds
    days    = 0
    sign    = "-"
  else:
    seconds = delta.seconds
    days    = delta.days
    sign    = ""
    
  hours = seconds / (60 * 60)
  minutes = (seconds - hours * 60 * 60) / 60
  seconds = seconds - hours * 60 * 60 - minutes * 60
  
  return "%sP%sT%s%s%s" % (
    sign,
    "%dD" % days if days else "",
    "%dH" % hours if hours else  "",
    "%dM" % minutes if minutes else  "",
    "%dS" % delta.seconds if (not days and not hours and not minutes) else "",
  )

def _date_diff(d1, d2):
  return owlready2.base._format_duration(datetime.date.fromisoformat(d1) - datetime.date.fromisoformat(d2))

def _date_add(d, td):
  return (datetime.date.fromisoformat(d) + owlready2.base._parse_duration(td)).isoformat()

def _date_sub(d, td):
  return (datetime.date.fromisoformat(d) - owlready2.base._parse_duration(td)).isoformat()

def _datetime_diff(d1, d2):
  return owlready2.base._format_duration(abs(datetime.datetime.fromisoformat(d1) - datetime.datetime.fromisoformat(d2)))

def _datetime_add(d, td):
  return (datetime.datetime.fromisoformat(d) + owlready2.base._parse_duration(td)).isoformat()

def _datetime_sub(d, td):
  return (datetime.datetime.fromisoformat(d) - owlready2.base._parse_duration(td)).isoformat()


class _Func(object):
  def __init__(self, world):
    self.world        = world
    self.last_nb_call = -1
    self.bns          = {}
    self.now          = None

  def _check_reset(self):
    if self.world._nb_sparql_call != self.last_nb_call:
      self.last_nb_call = self.world._nb_sparql_call
      self.bns = {}
      self.now = None
      
  def _now(self):
    self._check_reset()
    if self.now is None: self.now = datetime.datetime.now().isoformat()
    return self.now
  
  def _bnode(self, x = None):
    self._check_reset()
    if x is None:
      bn = self.world.new_blank_node()
    else:
      bn = self.bns.get(x)
      if not bn: bn = self.bns[x] = self.world.new_blank_node()
    return bn
  
  def _newinstanceiri(self, x):
    Class = self.world._get_by_storid(x)
    namespace = (owlready2.CURRENT_NAMESPACES.get() and owlready2.CURRENT_NAMESPACES.get()[-1]) or Class.namespace
    iri = self.world.graph._new_numbered_iri("%s%s" % (namespace.base_iri, Class.name.lower()))
    storid = self.world._abbreviate(iri)
    namespace.ontology._add_obj_triple_spo(storid, rdf_type, owl_named_individual)
    namespace.ontology._add_obj_triple_spo(storid, rdf_type, x)
    return storid
  
  def _loaded(self, x):
    return x in self.world._entities
  

def register_python_builtin_functions(world):
  if (sys.version_info.major == 3) and (sys.version_info.minor < 8):
    def create_function(name, num_params, func, deterministic = False):
      world.graph.db.create_function(name, num_params, func)
  else:
    create_function = world.graph.db.create_function
  create_function("md5",            1, _md5,      deterministic = True)
  create_function("sha1",           1, _sha1,     deterministic = True)
  create_function("sha256",         1, _sha256,   deterministic = True)
  create_function("sha384",         1, _sha384,   deterministic = True)
  create_function("sha512",         1, _sha512,   deterministic = True)
  create_function("seconds",        1, _seconds,  deterministic = True)
  create_function("tz",             1, _tz,       deterministic = True)
  create_function("timezone",       1, _timezone, deterministic = True)
  create_function("date_diff",      2, _date_diff, deterministic = True)
  create_function("date_add",       2, _date_add, deterministic = True)
  create_function("date_sub",       2, _date_sub, deterministic = True)
  create_function("datetime_diff",  2, _datetime_diff, deterministic = True)
  create_function("datetime_add",   2, _datetime_add, deterministic = True)
  create_function("datetime_sub",   2, _datetime_sub, deterministic = True)
  create_function("encode_for_uri", 1, urllib.parse.quote, deterministic = True)
  create_function("uuid",           0, _uuid)
  create_function("struuid",        0, _struuid)
  create_function("regex",         -1, _regex,          deterministic = True)
  create_function("sparql_replace",-1, _sparql_replace, deterministic = True)
  
  world._nb_sparql_call = 0
  func = _Func(world)
  create_function("now",             0, func._now, deterministic = True)
  create_function("bnode",          -1, func._bnode)
  create_function("newinstanceiri",  1, func._newinstanceiri)
  create_function("loaded",          1, func._loaded)
  
  # Unindexed table for deprioritizing subqueries
  world.graph.execute("""CREATE TEMP TABLE one (i INTEGER)""")
  world.graph.execute("""INSERT INTO one VALUES (1)""")

class FuncSupport(object):
  def parse_expression(self, expression):
    if   hasattr(expression, "sql"):   return " %s" % expression.sql
    elif isinstance(expression, list):
      if expression:
        if isinstance(expression[0], rply.Token) and expression[0].name == "FUNC":
          func = expression[0].value.upper()
          if   func == "CONTAINS":
            return "(INSTR(%s)!=0)" % self.parse_expression(expression[2])
          elif func == "STRSTARTS":
            x     = self.parse_expression(expression[2][0])
            start = self.parse_expression(expression[2][2]).strip()
            if start.startswith("'") and start.endswith("'") and not "'" in start[1:-1]:
              return "(SUBSTR(%s,1,%s)=%s)" % (x, len(start) - 2, start)
            else:
              return "(INSTR(%s,%s)=1)" % (x, start)
          elif func == "STRENDS":
            eo1 = self.parse_expression(expression[2][0])
            eo2 = self.parse_expression(expression[2][2])
            return "(SUBSTR(%s,-LENGTH(%s))=%s)" % (eo1, eo2, eo2)
          elif func == "STRBEFORE":
            eo1 = self.parse_expression(expression[2][0])
            eo2 = self.parse_expression(expression[2][2])
            return "SUBSTR(%s,1,INSTR(%s,%s)-1)" % (eo1, eo1, eo2)
          elif func == "STRAFTER":
            eo1 = self.parse_expression(expression[2][0])
            eo2 = self.parse_expression(expression[2][2])
            return "IIF(INSTR(%s,%s)=0,'',SUBSTR(%s,INSTR(%s,%s)+1))" % (eo1, eo2, eo1, eo1, eo2)
          elif func == "STR":
            eo         = self.parse_expression     (expression[2])
            e_type, ed = self.infer_expression_type(expression[2])
            if   e_type == "objs":  return "(SELECT iri FROM resources WHERE storid=%s)" % eo
            elif e_type == "datas": return "''||%s" % eo
            else:                   return "IIF(%s IS NULL, (SELECT iri FROM resources WHERE storid=%s), ''||%s)" % (ed, eo, eo)
          elif func == "HTTP://WWW.W3.ORG/2001/XMLSCHEMA#DOUBLE":
            eo = self.parse_expression(expression[2])
            return "CAST(%s AS DOUBLE)" % eo
          elif func == "HTTP://WWW.W3.ORG/2001/XMLSCHEMA#INTEGER":
            eo = self.parse_expression(expression[2])
            return "CAST(%s AS INTEGER)" % eo
          elif (func == "IRI") or (func == "URI"):
            eo         = self.parse_expression     (expression[2])
            e_type, ed = self.infer_expression_type(expression[2])
            if   e_type == "objs":  return eo
            elif e_type == "datas": return "(SELECT storid FROM resources WHERE iri=%s)" % eo
            else:                   return "IIF(%s IS NULL, %s, (SELECT storid FROM resources WHERE iri=%s))" % (ed, eo, eo)
          elif func == "LANG":
            eo         = self.parse_expression     (expression[2])
            e_type, ed = self.infer_expression_type(expression[2])
            return "IIF(SUBSTR(%s, 1, 1)='@', SUBSTR(%s, 2), '')" % (ed, ed)
          elif (func == "ISIRI") or (func == "ISURI"):
            eo         = self.parse_expression     (expression[2])
            e_type, ed = self.infer_expression_type(expression[2])
            if e_type == "objs": return "(%s > 0)" % eo
            else:                return "(%s IS NULL) & (%s > 0)" % (ed, eo)
          elif func == "ISBLANK":
            eo         = self.parse_expression     (expression[2])
            e_type, ed = self.infer_expression_type(expression[2])
            if e_type == "objs": return "(%s < 0)" % eo
            else:                return "(%s IS NULL) & (%s < 0)" % (ed, eo)
          elif func == "ISLITERAL":
            eo         = self.parse_expression     (expression[2])
            e_type, ed = self.infer_expression_type(expression[2])
            if   e_type == "objs":  return "0"
            elif e_type == "datas": return "1"
            else:                   return "NOT(%s IS NULL)" % ed
          elif func == "ISNUMERIC":
            eo         = self.parse_expression     (expression[2])
            e_type, ed = self.infer_expression_type(expression[2])
            if e_type == "objs":  return "0"
            else:                 return "(%s IN (43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 56, 57, 58, 59))" % ed
          elif func == "SAMETERM":
            eo1 = self.parse_expression(expression[2][0])
            eo2 = self.parse_expression(expression[2][2])
            return "(%s = %s)" % (eo1, eo2)
          elif func == "DATATYPE":
            eo         = self.parse_expression     (expression[2])
            e_type, ed = self.infer_expression_type(expression[2])
            return "IIF(TYPEOF(%s)='integer', %s, %s)" % (ed, ed, owlready2.rdf_langstring)
          elif func == "BOUND":
            return "(%s IS NOT NULL)" % self.parse_expression(expression[2])
          elif func == "YEAR":
            return "CAST(SUBSTR(%s, 1, 4) AS INTEGER)" % self.parse_expression(expression[2])
          elif func == "MONTH":
            return "CAST(SUBSTR(%s, 6, 2) AS INTEGER)" % self.parse_expression(expression[2])
          elif func == "DAY":
            return "CAST(SUBSTR(%s, 9, 2) AS INTEGER)" % self.parse_expression(expression[2])
          elif func == "HOURS":
            return "CAST(SUBSTR(%s, 12, 2) AS INTEGER)" % self.parse_expression(expression[2])
          elif func == "MINUTES":
            return "CAST(SUBSTR(%s, 15, 2) AS INTEGER)" % self.parse_expression(expression[2])
          elif func == "CEIL":
            eo = self.parse_expression(expression[2])
            return "(CAST(%s AS INTEGER)+IIF(%s<0.0,0.0,IIF(CAST(%s AS INTEGER)=%s,0.0,1.0)))" % (eo, eo, eo, eo)
          elif func == "FLOOR":
            eo = self.parse_expression(expression[2])
            return "(CAST(%s AS INTEGER)+IIF(%s<0.0,IIF(CAST(%s AS INTEGER)=%s,0.0,-1.0),0.0))" % (eo, eo, eo, eo)
          elif func == "RAND":
            return "((RANDOM() + 9223372036854775808) / 18446744073709551615)"
          elif func == "LANGMATCHES":
            eo1          = self.parse_expression     (expression[2][0])
            e1_type, ed1 = self.infer_expression_type(expression[2][0])
            eo2          = self.parse_expression     (expression[2][2]).strip()
            if   eo2 == "'*'":
              return "TYPEOF(%s)='text'" % ed1
            elif eo2.startswith("'") and (len(eo2) <= 4):
              return "SUBSTR(%s,2,2)=LOWER(%s)" % (ed1, eo2)
            else:
              return "IIF(%s='*',TYPEOF(%s)='text',SUBSTR(%s,2,2)=LOWER(%s))" % (eo2, ed1, ed1, eo2)
          elif func == "STRDT":
            return self.parse_expression(expression[2][0])
          elif func == "STRLANG":
            return self.parse_expression(expression[2][0])
          elif func == "SAMPLE":
            return "MIN(%s)" % self.parse_expression(expression[3])
          elif func == "STORID":
            return self.parse_expression(expression[2][0])
        elif isinstance(expression[0], rply.Token) and expression[0].name == "ASC":
          return "%s ASC" % self.parse_expression(expression[1][1])
        elif isinstance(expression[0], rply.Token) and expression[0].name == "DESC":
          return "%s DESC" % self.parse_expression(expression[1][1])
          
        return "".join(self.parse_expression(i) for i in expression) 
    elif expression is None: pass
    elif expression.name  == "VAR":
      #print(expression, self.vars, self.parse_var(expression))
      
      return self.parse_var(expression).get_binding(self)
    elif expression.name  == "PARAM":  return "?%s" % expression.number
    elif expression.value == "(":      return "("
    elif expression.value == ")":      return ")"
    else:                              return " %s" % expression.value
    return ""
  
  def infer_expression_type(self, expression, accept_zero = False):
    if isinstance(expression, list):
      if expression and isinstance(expression[0], rply.Token):
        if   expression[0].name == "FUNC":
          func = expression[0].value.upper()
          if   func == "IF":
            a1, a2 = self.infer_expression_type(expression[2][2], accept_zero)
            b1, b2 = self.infer_expression_type(expression[2][4], accept_zero)
            if accept_zero:
              if a1 != b1: return "quads", 0
              if a2 != b2: return a1, 0
              return a1, a2
            else:
              if a1 != b1: a1 = "quads"
              if a2 != b2: return a1, "IIF(%s,%s,%s)" % (self.parse_expression(expression[2][0]), a2, b2)
              return a1, a2
          elif func == "COALESCE":
            return self.infer_expression_type(expression[2][0], accept_zero)
          elif func == "CONCAT":
            #return "data", self.infer_expression_type(expression[2][0], accept_zero)[1]
            d = 0
            for i, arg in enumerate(expression[2]):
              if i % 2 != 0: continue
              d = self.infer_expression_type(arg, accept_zero)[1]
              if isinstance(d, str): break
            return "datas", d
          elif (func == "UCASE") or (func == "LCASE") or (func == "STRBEFORE") or (func == "STRAFTER") or (func == "SUBSTR") or (func == "REPLACE") or (func == "SIMPLEREPLACE") or (func == ""):
            return self.infer_expression_type(expression[2][0], accept_zero)
          elif func == "STRDT":
            return "datas", self.parse_expression(expression[2][2])
          elif func == "STRLANG":
            return "datas", "'@'||%s" % self.parse_expression(expression[2][2])
          elif func == "TIMEZONE":
            return "datas", self.translator.world._abbreviate("http://www.w3.org/2001/XMLSchema#dayTimeDuration")
          elif func == "ABS":
            return self.infer_expression_type(expression[2][0], accept_zero)
          elif func == "SAMPLE":
            return self.infer_expression_type(expression[3], accept_zero)
          else:
            datatype = _FUNC_2_DATATYPE[func]
            if datatype is None: return "objs", "NULL"
            return "datas", datatype
          
      for i in expression:
        name = getattr(i, "name", "")
        if name in _BOOL_EXPRESSION_MEMBERS:   return "datas", _universal_datatype_2_abbrev[bool]
        if name in _NUMBER_EXPRESSION_MEMBERS:
          vars = []
          for i in expression:
            a1, a2 = self.infer_expression_type(i, accept_zero)
            if a2 in (56, 58, 59): # decimal, float, real
              return "datas", _universal_datatype_2_abbrev[float]
            if isinstance(a2, str): vars.append(a2)
            
          ints = {43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54}
          if   len(vars) == 0: return "datas", _universal_datatype_2_abbrev[int]
          elif len(vars) == 1: return "datas", vars[0]
            
      r1 = set()
      r2 = set()
      for i in expression:
        if isinstance(i, list) and not i: continue
        a1, a2 = self.infer_expression_type(i, accept_zero)
        if not a1 is None:
          r1.add(a1)
          r2.add(a2)
      if len(r1) != 1: return "quads", 0
      if len(r2) != 1: return tuple(r1)[0], 0
      return tuple(r1)[0], tuple(r2)[0]
    
    elif  expression is None: pass
    elif  expression.name == "STRING":  return "datas", _universal_datatype_2_abbrev[str]
    elif  expression.name == "INTEGER": return "datas", _universal_datatype_2_abbrev[int]
    elif (expression.name == "FLOAT") or (expression.name == "DECIMAL"): return "datas", _universal_datatype_2_abbrev[float]
    elif  expression.name == "VAR":
      var = self.parse_var(expression)
      if var.type == "objs": return "objs", "NULL"
      return var.type, "%sd" % var.get_binding(self)[:-1]
    elif  expression.name == "PARAM":
      return "quads", "%sTypeOfParam?%s " % (self.translator.escape_mark, expression.number)
    return None, None
  
