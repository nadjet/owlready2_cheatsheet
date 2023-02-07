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


import sys, os, re, math
from owlready2 import *
from owlready2.sparql.parser import *
from owlready2.sparql.func   import register_python_builtin_functions, FuncSupport

_RE_AUTOMATIC_INDEX = re.compile(r"([^ ]*?) USING AUTOMATIC.*\((.*?)\)")
#_RE_NORMAL_INDEX    = re.compile(r"(.*?) AS (.*?) USING (COVERING )?INDEX (.*?) ")

_DEPRIORIZE_SUBQUERIES_OPT = True

class Translator(object):
  def __init__(self, world, error_on_undefined_entities = True):
    self.world                         = world
    self.error_on_undefined_entities   = error_on_undefined_entities
    self.prefixes                      = { "rdf:" : "http://www.w3.org/1999/02/22-rdf-syntax-ns#", "rdfs:" : "http://www.w3.org/2000/01/rdf-schema#", "owl:" : "http://www.w3.org/2002/07/owl#", "xsd:" : "http://www.w3.org/2001/XMLSchema#", "obo:" : "http://purl.obolibrary.org/obo/", "owlready:" : "http://www.lesfleursdunormal.fr/static/_downloads/owlready_ontology.owl#" }
    self.base_iri                      = ""
    self.current_anonynous_var         = 0
    self.current_parameter             = 0
    self.max_fixed_parameter           = 0
    self.main_query                    = None
    self.preliminary_selects           = []
    self.recursive_preliminary_selects = {}
    self.escape_mark                   = "@@@ESCAPE@@@"
    self.next_table_id                 = 1
    self.table_name_2_type             = {}
    self.table_type_2_cols             = { "objs" : ["s", "p", "o"], "datas" : ["s", "p", "o", "d"], "quads" : ["s", "p", "o", "d"] , "one" : ["i"] }
    
    if not getattr(world.graph, "_has_sparql_func", False):
      register_python_builtin_functions(world)
      world.graph._has_sparql_func = True
      
  def make_translator(self):
    translator = Translator(self.world, self.error_on_undefined_entities)
    translator.prefixes = self.prefixes.copy()
    translator.base_iri = self.base_iri
    return translator
  
  def parse(self, sparql):
    while self.escape_mark in sparql:
      self.escape_mark += "ç"
    CURRENT_TRANSLATOR.set(self)
    self.main_query = PARSER.parse(LEXER.lex(sparql))
    return self.finalize()
    
  def finalize(self):
    sql = ""
    if self.preliminary_selects:
      sql += "WITH "
      if max(prelim.recursive for prelim in self.preliminary_selects): sql += "RECURSIVE "
      sql += ",\n\n".join(prelim.sql() for prelim in self.preliminary_selects)
      sql += "\n\n"

    sql += self.main_query.sql()
    
    if self.solution_modifier[0]:
      sql += " GROUP BY %s" % ", ".join(self.main_query.parse_expression(x) for x in self.solution_modifier[0])
    if self.solution_modifier[1]:
      sql += " HAVING %s" % self.main_query.parse_expression(self.solution_modifier[1])
    if self.solution_modifier[2]:
      sql += " ORDER BY %s" % ", ".join(self.main_query.parse_expression(x) for x in self.solution_modifier[2])
    if self.solution_modifier[3]:
      sql += " LIMIT %s"  % self._to_sql(self.solution_modifier[3])
    if self.solution_modifier[4]:
      if not self.solution_modifier[3]: sql += " LIMIT -1" # SQLite requires a LIMIT clause before the OFFSET clause
      sql += " OFFSET %s" % self._to_sql(self.solution_modifier[4])
      
    nb_parameter = max(self.current_parameter, self.max_fixed_parameter)
    parameter_2_parameter_datatypes = {}
    parameter_datatypes = []
    if self.escape_mark in sql:
      def sub(m):
        escape = m.group(0)[len(self.escape_mark):]
        if escape.startswith("TypeOfParam?"):
          number = int(escape[12:])
          r = parameter_2_parameter_datatypes.get(number)
          if r is None:
            r = parameter_2_parameter_datatypes[number] = self.new_parameter()
            parameter_datatypes.append(number - 1)
        return "?%s" % r
      sql = re.sub("%s[^ ]*" % self.escape_mark, sub, sql)
      
    #if sql:
    #  if   self.main_query.type == "select": nb_sql_parameter = nb_parameter + len(parameter_datatypes)
    #  else:                                  nb_sql_parameter = len(self.main_query.select_param_indexes)
    #  sql = self.optimize_sql(sql, nb_sql_parameter)
    
    if   self.main_query.type == "select":
      return PreparedSelectQuery(self.world, sql, [column.var for column in self.main_query.columns if not column.name.endswith("d")], [column.type for column in self.main_query.columns], nb_parameter, parameter_datatypes)
    
    elif self.main_query.type == "modify":
      select_param_indexes = [i - 1 for i in self.main_query.select_param_indexes]
      return PreparedModifyQuery(self.world, sql, [column.var for column in self.main_query.columns if not column.name.endswith("d")], [column.type for column in self.main_query.columns], nb_parameter, parameter_datatypes, self.world.get_ontology(self.main_query.ontology_iri.value) if self.main_query.ontology_iri else None, self.parse_inserts_deletes(self.main_query.deletes, self.main_query.columns), self.parse_inserts_deletes(self.main_query.inserts, self.main_query.columns), select_param_indexes)
    
    
  def optimize_sql(self, sql, nb_sql_parameter):
    plan = list(self.world.graph.execute("""EXPLAIN QUERY PLAN %s""" % sql, (1,) * nb_sql_parameter))
                
    has_automatic_index = False
    for l in plan:
      match = _RE_AUTOMATIC_INDEX.search(l[3])
      if match:
        table_name = match.group(1)
        index_name = match.group(2)
        table_type = self.table_name_2_type.get(table_name)
        
        if (table_type == "objs") or (table_type == "datas"):
          if   index_name.startswith("s="): index_name = "index_%s_sp" % table_type
          elif index_name.startswith("o="): index_name = "index_%s_op" % table_type
          else: continue
          
          print("OPTIMIZE!!!", l, table_type, table_name, "=>", index_name)
          table_def = "%s %s" % (table_type, table_name)
          sql = sql.replace(table_def, "%s INDEXED BY %s" % (table_def, index_name), 1)
    return sql
    
  # def optimize_sql(self, sql):
  #   # Avoid Sqlite3 AUTOMATIC INDEX when a similar index can be used.
  #   plan = list(self.world.graph.execute("""EXPLAIN QUERY PLAN %s""" % sql))
  #   #for l in plan:
  #     #if (" USING AUTOMATIC " in l[3]) and not (" TABLE " in l[3]): break
  #   #else:
  #   try:
  #     self.world.graph.execute("PRAGMA automatic_index = false")
  #     plan = list(self.world.graph.execute("""EXPLAIN QUERY PLAN %s""" % sql))
  #   finally:
  #     self.world.graph.execute("PRAGMA automatic_index = true")
      
  #   for l in plan:
  #       match = _RE_NORMAL_INDEX.search(l[3])
  #       if match:
  #         table_type = match.group(1)
  #         table_name = match.group(2)
  #         index_name = match.group(4)
  #         if table_name == "q": continue # Recursive hard-coded preliminary queries
  #         #if ("%s INDEXED" % table_name) in sql: continue
  #         table_def = "%s %s" % (table_type, table_name)
  #         #print("OPTIMIZE!!!", l, table_type, table_name, index_name)
  #         sql = sql.replace(table_def, "%s INDEXED BY %s" % (table_def, index_name), 1)
  #   return sql
    
  
  def parse_inserts_deletes(self, triples, columns):
    var_2_column = { column.var : column for column in self.main_query.columns if not column.name.endswith("d") }
    r = []
    for triple0 in triples:
      triple = []
      for x in triple0:
        if   hasattr(x, "storid"):
          triple.append(("objs", x.storid))
        elif x.name == "VAR":
          if x.value.startswith("??anon") or x.value.startswith("_:"): # a new blank node
            triple.append(("bn", x.value))
          else: # a normal var
            column = var_2_column[x.value]
            triple.append(("vars", column.index))
            if len(triple) == 3: # in 'o' position => can be objs or datas!
              if column.index + 1 < len(columns):
                next_column = columns[column.index + 1]
                if next_column.name.endswith("d"):
                  triple.append(("vars", next_column.index))
        elif x.name == "PARAM":
          triple.append(("param", x.number - 1))
          if len(triple) == 3: # in 'o' position => can be datas!
            triple.append(("paramdatatype", x.number - 1))
        else:
          if   isinstance(x.value, locstr):
            triple.append(("datas", x.value[1:-1]))
            triple.append(("datas", "@%s" % x.value.lang))
          else:
            if isinstance(x.value, str): v, d = self.world._to_rdf(x.value[1:-1])
            else:                        v, d = self.world._to_rdf(x.value)
            d2 = getattr(x, "datatype", None) or d
            triple.append(("datas", v))
            triple.append(("datas", d2))
            
      r.append(triple)

    return r
  
  def new_sql_query(self, name, block, selects = None, distinct = None, solution_modifier = None, preliminary = False, extra_binds = None, nested_inside = None, copy_vars = False):
    if preliminary and not name: name = "prelim%s" % (len(self.preliminary_selects) + 1)
    
    if isinstance(block, UnionBlock) and block.simple_union_triples:
      block = SimpleTripleBlock(block.simple_union_triples)
      
    if   isinstance(block, SimpleTripleBlock):
      s = SQLQuery(name)
      
    elif isinstance(block, OptionalBlock):
      s = SQLQuery(name)
      s.optional = True
      
    elif isinstance(block, UnionBlock):
      s = SQLCompoundQuery(name, nested_inside)
      if selects is None:
        selects = block.get_ordered_vars()
        
    elif isinstance(block, FilterBlock):
      s = SQLNestedQuery(name)
      #if isinstance(block, ExistsBlock): s.extra_sql = "IS NOT NULL"
      #else:                              s.extra_sql = "IS NULL"
      s.exists = isinstance(block, ExistsBlock)
      if nested_inside: s.vars = nested_inside.vars
      preliminary = False
      
    elif isinstance(block, NotExistsBlock):
      s = SQLCompoundQuery(name, nested_inside)
      
    elif isinstance(block, SubQueryBlock):
      s = block.parse()
      s.name = "prelim%s" % (len(self.preliminary_selects) + 1)
      
    else:
      raise ValueError("Unknown block type '%s'!" % block)
    
    if preliminary:
      s.preliminary = True
      self.preliminary_selects.append(s)
      
      
    # if copy_vars:
    #   if hasattr(nested_inside, "vars"):
    #     s.vars = nested_inside.vars.copy()
    #   elif hasattr(nested_inside, "parent") and nested_inside.parent:
    #     s.vars = nested_inside.parent.vars.copy()

        
    extra_binds = extra_binds or []
    if isinstance(selects, list): # Otherwise, it is "SELECT *"
      for i, select in enumerate(selects):
        if isinstance(select, list): # ( expression AS var )
          selects[i] = select[2]
          bind = Bind(select[0], select[2])
          extra_binds.append(bind)
          
          
    if   isinstance(block, (SimpleTripleBlock, OptionalBlock, FilterBlock)):
      s.parse_distinct(distinct)
      
      for i in block:
        if isinstance(i, Bind): s.prepare_bind(i)
      for bind in extra_binds: s.prepare_bind(bind)
      
      s.parse_selects(selects)

      s.parse_triples(block)
      for bind in extra_binds: s.parse_bind(bind)
      
      s.finalize_columns()
      
    elif isinstance(block, UnionBlock):
      for alternative in block:
        query = self.new_sql_query(None, alternative, selects, distinct, None, False, extra_binds, nested_inside = s, copy_vars = False)
        s.append(query, "UNION")
      s.finalize_compounds()
      
      
    if (not preliminary) and solution_modifier: self.solution_modifier = solution_modifier
    return s

  def expand_prefix(self, prefix):
    expanded = self.prefixes.get(prefix)
    if expanded: return expanded
    prefix0 = prefix[:-1] # Remove trailing :
    for ontology in self.world.ontologies.values():
      if prefix0 == ontology.name:
        self.prefixes[prefix] = ontology.base_iri
        return ontology.base_iri
    raise ValueError("Undefined prefix '%s'!" % prefix)

  def abbreviate(self, entity):
    if self.error_on_undefined_entities:
      r = self.world._abbreviate(entity, False)
      if r is None: raise ValueError("No existing entity for IRI '%s'! (use error_on_undefined_entities=False to accept unknown entities in SPARQL queries)" % entity)
      return r
    else:
      return self.world._abbreviate(entity)
  
  def _to_sql(self, x):
    if x.name == "PARAM": return "?%s" % x.number
    return x.value
    
  def new_var(self):
    self.current_anonynous_var += 1
    return "??anon%s" % self.current_anonynous_var

  def new_parameter(self):
    self.current_parameter += 1
    return self.current_parameter
  
  def get_recursive_preliminary_select(self, triple, fixed, fixed_var, prelim_triples):
    prelim = self.recursive_preliminary_selects.get((triple, fixed, fixed_var, tuple(prelim_triples)))
    if not prelim:
      self.recursive_preliminary_selects[triple, fixed, fixed_var, tuple(prelim_triples)] = prelim = SQLRecursivePreliminaryQuery("prelim%s" % (len(self.preliminary_selects) + 1), triple, fixed, fixed_var)
      self.preliminary_selects.append(prelim)
      prelim.build(triple, prelim_triples)
    return prelim


class PreparedQuery(object):
  def __init__(self, world, sql, column_names, column_types, nb_parameter, parameter_datatypes):
    self.world               = world
    self.sql                 = sql
    self.column_names        = column_names
    self.column_types        = column_types
    self.nb_parameter        = nb_parameter
    self.parameter_datatypes = parameter_datatypes
    
  def execute(self, params = ()):
    self.world._nb_sparql_call += 1
    sql_params = [self.world._to_rdf(param)[0] for param in params]
    for i in self.parameter_datatypes: sql_params.append(self.world._to_rdf(params[i])[1])
    return self.world.graph.execute(self.sql, sql_params)
  
class PreparedSelectQuery(PreparedQuery):
  def execute(self, params = ()):
    for l in PreparedQuery.execute(self, params):
      l2 = []
      i = 0
      while i < len(l):
        if self.column_types[i] == "objs":
          if l[i] is None: l2.append(None)
          else: l2.append(self.world._to_python(l[i], None) or l[i])
          i += 1
        else:
          if l[i + 1] is None:
            if l[i] is None: l2.append(None)
            else:            l2.append(self.world._to_python(l[i], None) or l[i])
          else:
            l2.append(self.world._to_python(l[i], l[i + 1]))
          i += 2
      yield l2
      
  def _execute_sql(self, params = ()):
    for l in PreparedQuery.execute(self, params):
      l2 = []
      i = 0
      while i < len(l):
        #if self.column_types[i] == "objs":
        if (self.column_types[i] == "objs") or (self.column_types[i] == "value"):
          l2.append(l[i])
          i += 1
        else:
          if l[i + 1] is None:
            if l[i] is None: v = None
            else:            v = self.world._to_python(l[i], None) or l[i]
          else:
            v = self.world._to_python(l[i], l[i + 1])
          if isinstance(v, str): l2.append("'%s'" % v.replace("'", "\\'"))
          else:                  l2.append(v)
          i += 2
      yield l2
      
  def execute_flat(self, params = ()):
    for l in PreparedQuery.execute(self, params):
      i = 0
      while i < len(l):
        if self.column_types[i] == "objs":
          if l[i] is None: l2.append(None)
          else: yield self.world._to_python(l[i], None) or l[i]
          i += 1
        else:
          if l[i + 1] is None:
            if l[i] is None: l2.append(None)
            else:            l2.append(self.world._to_python(l[i], None) or l[i])
          else:
            yield self.world._to_python(l[i], l[i + 1])
          i += 2
          
  def execute_csv(self, params = (), separator = ","):
    import csv, io
    b = io.StringIO()
    f = csv.writer(b, delimiter = separator)
    f.writerow(col[1:] for col in self.column_names)
    rows = []

    for l in PreparedQuery.execute(self, params):
      l2 = []
      i = 0
      while i < len(l):
        if self.column_types[i] == "objs":
          if   l[i] is None: l2.append("")
          elif l[i] > 0:     l2.append(self.world._unabbreviate(l[i]))
          else:              l2.append("_:%s" % (-l[i]))
          i += 1
        else:
          if l[i + 1] is None:
            if   l[i] is None: l2.append("")
            elif l[i] > 0:     l2.append(self.world._unabbreviate(l[i]))
            else:              l2.append("_:%s" % (-l[i]))
          else:
            l2.append(str(self.world._to_python(l[i], l[i + 1])))
          i += 2
      f.writerow(l2)
    return b.getvalue()
  
  def execute_tsv(self, params = ()): return self.execute_csv(params, "\t")

  def execute_json(self, params = ()):
    bindings = []
    colnames = [col[1:] for col in self.column_names]
    json = { "head" : { "vars" : colnames },
             "results" : { "bindings" : bindings } }
    for l in PreparedQuery.execute(self, params):
      binding = {}
      bindings.append(binding)
      i = 0
      c = 0
      while i < len(l):
        if self.column_types[i] == "objs":
          if   l[i] is None: pass
          elif l[i] > 0:     binding[colnames[c]] = { "type" : "uri", "value" : self.world._unabbreviate(l[i]) }
          else:              binding[colnames[c]] = { "type" : "bnode", "value" : "r%s" % (-l[i]) }
          i += 1
        else:
          if l[i + 1] is None:
            if   l[i] is None: pass
            elif l[i] > 0:     binding[colnames[c]] = { "type" : "uri", "value" : self.world._unabbreviate(l[i]) }
            else:              binding[colnames[c]] = { "type" : "bnode", "value" : "r%s" % (-l[i]) }
          else:
            value = str(self.world._to_python(l[i], l[i + 1]))
            if   isinstance(l[i + 1], str): binding[colnames[c]] = { "type" : "literal", "value" : value, "xml:lang" : l[i + 1][1:] }
            elif l[i + 1]:                  binding[colnames[c]] = { "type" : "literal", "value" : value, "datatype" : self.world._unabbreviate(l[i + 1]) }
            else:                           binding[colnames[c]] = { "type" : "literal", "value" : value }
          i += 2
        c += 1
    return repr(json)

  def execute_xml(self, params = ()):
    bindings = []
    colnames = [col[1:] for col in self.column_names]
    xml = """<?xml version="1.0"?>
<sparql xmlns="http://www.w3.org/2005/sparql-results#">
  <head>
"""
    for colname in colnames:
      xml += """    <variable name="%s"/>\n""" % colname
    xml += """  </head>
  <results>
"""
    
    for l in PreparedQuery.execute(self, params):
      xml += """    <result>\n"""
      i = 0
      c = 0
      while i < len(l):
        xml += """      <binding name="%s">\n""" % colnames[c]
        if self.column_types[i] == "objs":
          if   l[i] is None: pass
          elif l[i] > 0:     xml += """        <uri>%s</uri>\n""" % self.world._unabbreviate(l[i])
          else:              xml += """        <bnode>r%s</bnode>\n""" % (-l[i])
          i += 1
        else:
          if l[i + 1] is None:
            if   l[i] is None: pass
            elif l[i] > 0:     xml += """        <uri>%s</uri>\n""" % self.world._unabbreviate(l[i])
            else:              xml += """        <bnode>r%s</bnode>\n""" % (-l[i])
          else:
            value = str(self.world._to_python(l[i], l[i + 1]))
            if   isinstance(l[i + 1], str): xml += """        <literal xml:lang="%s">%s</literal>\n""" % (l[i + 1][1:], value)
            elif l[i + 1]:                  xml += """        <literal datatype="%s">%s</literal>\n""" % (self.world._unabbreviate(l[i + 1]), value)
            else:                           xml += """        <literal>%s</literal>\n""" % value
          i += 2
        c += 1
        xml += """      </binding>\n"""
      xml += """    </result>\n"""
        
    xml += """  </results>
</sparql>
"""
    return xml
  
  def execute_as_sql(self, params = ()):
    for l in PreparedQuery.execute(self, params):
      l2 = []
      i = 0
      while i < len(l):
        if self.column_types[i] == "objs":
          if l[i] is None: l2.append(None)
          else: l2.append(self.world._to_python(l[i], None) or l[i])
          i += 1
        else:
          if l[i + 1] is None:
            if l[i] is None: l2.append(None)
            else:            l2.append(self.world._to_python(l[i], None) or l[i])
          else:
            l2.append(self.world._to_python(l[i], l[i + 1]))
          i += 2
      yield l2
      
  
class PreparedModifyQuery(PreparedQuery):
  def __init__(self, world, sql, column_names, column_types, nb_parameter, parameter_datatypes, ontology, deletes, inserts, select_param_indexes):
    PreparedQuery.__init__(self, world, sql, column_names, column_types, nb_parameter, parameter_datatypes)
    
    column_name_2_index = { column_name : i for (i, column_name) in enumerate(column_names) }
    self.ontology = ontology
    self.deletes  = deletes
    self.inserts  = inserts
    self.select_param_indexes = select_param_indexes
    
  def execute(self, params = ()):
    nb_match = 0
    if self.sql: resultss = PreparedQuery.execute(self, [params[i] for i in self.select_param_indexes])
    else:        resultss = [()]
    
    added_triples = []
    for results in set(resultss):
      nb_match += 1
      
      for delete in self.deletes:
        triple = []
        for type, value in delete:
          if   type == "vars":          triple.append(results[value])
          elif type == "param":         triple.append(self.world._to_rdf(params[value])[0])
          elif type == "paramdatatype": triple.append(self.world._to_rdf(params[value])[1])
          else:                         triple.append(value)
        #print("DEL", triple)
        self.world._del_triple_with_update(*triple)
        
      bns = {}
      for insert in self.inserts:
        triple = []
        for type, value in insert:
          if   type == "vars":          triple.append(results[value])
          elif type == "bn":            triple.append(bns.get(value) or bns.setdefault(value, self.world.new_blank_node()))
          elif type == "param":         triple.append(self.world._to_rdf(params[value])[0])
          elif type == "paramdatatype": triple.append(self.world._to_rdf(params[value])[1])
          else:                         triple.append(value)
        #print("ADD", insert, triple)
        added_triples.append(triple)
        
    if added_triples: self.world._add_triples_with_update(self.ontology, added_triples)
    return nb_match
  
    
class Column(object):
  def __init__(self, var, type, binding, name, index):
    self.var         = var
    self.type        = type
    self.binding     = binding
    self.name        = name
    self.index       = index
    
  def __repr__(self):
    return """<Column #%s %s %s %s %s>""" % (self.index, self.var, self.type, self.binding, self.name)
    
class Variable(object):
  def __init__(self, name):
    self.name           = name
    self.type           = "quads"
    self.fixed_datatype = None
    self.prop_type      = "quads" # Type when the variable is used as a property
    self.bindings       = []
    self.bind           = None
    self.initial_query  = None
    self.nb_table       = 0
    
  def __repr__(self): return """<Variable %s type %s, %s bindings>""" % (self.name, self.type, len(self.bindings))
  
  def get_binding(self, query):
    if not self.bindings:
      #print("* Owlready2 * WARNING: variable without binding in SPARQL, use a suboptimal option", file = sys.stderr)
      table = Table(query, "any%s" % query.translator.next_table_id, """(SELECT DISTINCT s AS o, NULL AS d FROM quads UNION SELECT DISTINCT o, d FROM quads)""")
      table.subquery = query
      query.translator.next_table_id += 1
      self.bindings.append("%s.o" % table.name)
    i = 0
    for binding in self.bindings:
      if not binding.startswith("IN "): break
    return binding
  
  def update_type(self, type):
    if   self.type == "quads": self.type = type
    elif (type != self.type) and (type != "quads"):
      raise ValueError("Variable %s cannot be both %s and %s!\n\n(NB if you are querying entities that are objects of a rdfs:label or comment relations, please add the following code to prevent Owlready from assuming that label and comment are data and not entities:\n    import owlready2.sparql.parser\n    owlready2.sparql.parser._DATA_PROPS = set()\n)" % (self.name, self.type, type))
    
class Table(object):
  def __init__(self, query, name, type = "quads", index = None, join = ",", join_conditions = None):
    self.name            = name
    self.type            = type
    self.index           = index
    self.join            = join
    self.join_conditions = join_conditions or []
    self.subquery        = None
    if query:
      query.tables.append(self)
      query.name_2_table[name] = self
      query.translator.table_name_2_type[name] = type
      
  def __repr__(self): return "<Table '%s %s'>" % (self.type, self.name)
  
  def sql(self):
    return """%s %s%s%s""" % (self.type, self.name, self.index and (" INDEXED BY %s" % self.index) or "", self.join_conditions and (" ON (%s)" % " AND ". join(self.join_conditions)) or "")
  
  
class SQLQuery(FuncSupport):
  def __init__(self, name):
    self.name                     = name
    self.preliminary              = False
    self.recursive                = False
    self.translator               = CURRENT_TRANSLATOR.get()
    self.distinct                 = False
    self.raw_selects              = None
    self.tables                   = []
    self.name_2_table             = {}
    self.columns                  = []
    self.conditions               = []
    self.triples                  = []
    self.vars_needed_for_select   = set()
    self.vars                     = {}
    self.extra_sql                = ""
    self.select_simple_union      = False
    self.optional                 = False
    
    
  def __repr__(self): return "<%s '%s'>" % (self.__class__.__name__, self.sql())

  def _find_join_preceding_table(self, table):
    if table.join == ",": return None
    for condition in table.join_conditions:
      parts = condition.split("=", 1)
      if len(parts) == 2:
        preceding = self.name_2_table.get(parts[1].split(".", 1)[0])
        if preceding: return preceding
        
  def sql(self):
    if self.tables:
      sql = """SELECT """
      if self.distinct: sql += "DISTINCT "
      sql += """%s FROM """ % (", ".join(str(column.binding) for column in self.columns))
      
      table_2_preceding = {}
      for table in self.tables:
        preceding = self._find_join_preceding_table(table)
        if preceding: table_2_preceding[table] = preceding
        
      if table_2_preceding:
        tables = list(self.tables)
        for table, preceding in table_2_preceding.items():
          table_i     = tables.index(table)
          preceding_i = tables.index(preceding)
          if table_i < preceding_i:
            tables.remove(table)
            tables.insert(tables.index(preceding) + 1, table)
        self.tables = tables
        
      if self.tables[0].join != ",": # Cannot JOIN on the first table
        for table in self.tables:
          if table.join == ",":
            self.tables.remove(table)
            self.tables.insert(0, table)
            break
          
      for table in self.tables:
        if not table is self.tables[0]: sql += " %s " % table.join
        sql += table.sql()
      if self.conditions:
        sql += """ WHERE %s""" % (" AND ".join(str(condition) for condition in self.conditions))
    else:
      if not self.columns: return ""
      if self.select_simple_union:
        for i, column in enumerate(self.columns):
          if isinstance(column.binding, list): break
        l = []
        for j in range(len(self.columns[i].binding)):
          l.append([])
          for k, column in enumerate(self.columns):
            if k == i: l[-1].append(column.binding[j])
            else:      l[-1].append(column.binding)
        sql = """VALUES %s""" % ",".join("(%s)" % ",".join(str(k) for k in j) for j in l)
      else:
        vars = []
        for column in self.columns:
          if isinstance(column.binding, str) and column.binding.startswith("IN "):
            var = self.parse_var(column.var)
            vars.append(var)
        if vars:
          if hasattr(vars[0], "static"):
            sql = """VALUES %s""" % ",".join("(%s)" % (",".join(str(value) for value in values)) for values in zip(*[[i[0] for i in var.static] for var in vars]))
          else:
            sql = """SELECT %s FROM %s""" % (",".join("%s.col1_o" % var.in_select.name for var in vars), ",".join(var.in_select.name for var in vars))
        else:
          sql = """VALUES (%s)""" % (",".join(str(column.binding) for column in self.columns))
        
    if self.extra_sql: sql += " %s" % self.extra_sql
    if self.preliminary:
      return """%s(%s) AS (%s)""" % (self.name, ", ".join(column.name for column in self.columns), sql)
    return sql
    
  def parse_distinct(self, distinct):
    if isinstance(distinct, rply.Token): self.distinct = distinct and (distinct.value.upper() == "DISTINCT")
    else:                                self.distinct = distinct
    
  def parse_var(self, x):
    if isinstance(x, Variable):   return x
    if isinstance(x, rply.Token): name = x.value
    else:                         name = x
    var = self.vars.get(name)
    if not var: self.vars[name] = var = Variable(name)
    return var
  
  def parse_selects(self, selects):
    if selects is None:
      self.raw_selects = "*"
    else:
      self.raw_selects = selects
      vars_needed_for_select = { self.parse_var(select) for select in selects if (isinstance(select, rply.Token) and (select.name == "VAR")) or (isinstance(select, str)) }
      for var in vars_needed_for_select:
        self.expand_referenced_vars(var, self.vars_needed_for_select)
        
  def expand_referenced_vars(self, var, r):
    r.add(var)
    if var.bind:
      for var_name in var.bind.referenced_var_names:
        self.expand_referenced_vars(self.parse_var(var_name), r)
        
  def prepare_bind(self, bind):
    var      = self.parse_var(bind.var)
    var.bind = bind
    
  def parse_bind(self, bind):
    var      = self.parse_var(bind.var)
    var.bind = bind
    var.bindings.insert(0, self.parse_expression(bind.expression))
    
    fixed_type, fixed_datatype = self.infer_expression_type(bind.expression, accept_zero = True)
    if fixed_type is None: fixed_type = "quads"
    var.update_type(fixed_type)
    if fixed_type != "objs":  var.fixed_datatype = fixed_datatype
    
  def parse_filter(self, filter):
    sql = self.parse_expression(filter.constraint)
    self.conditions.append(sql)
              
  def add_subquery(self, sub):
    if isinstance(sub, SQLNestedQuery):
      self.conditions.append(sub)
      if _DEPRIORIZE_SUBQUERIES_OPT and not ("one" in self.name_2_table): Table(self, "one", "one")
    else:
      ok = self.try_create_in_conditions(self.conditions, sub.columns[0].var, sub) # Try specific optimization with IN operator
      if not ok:
        table = Table(self, "p%s" % self.translator.next_table_id, sub.name)
        table.subquery = sub
        self.translator.next_table_id += 1
        if sub.optional:
          table.join = "LEFT JOIN"
          conditions = table.join_conditions
        else:
          conditions = self.conditions
          
        for column in sub.columns:  
          var = self.parse_var(column.var)
          var.update_type(column.type)
          if not column.name.endswith("d"):
            self.create_conditions(conditions, table, column.name, var)

  def parse_triples(self, triples):
    if self.triples: raise ValueError("Cannot parse triples twice!")
    self.block = triples
    self.triples.extend(triples)
    
    if self.raw_selects is None: raise ValueError("Need to call parse_selects() before finalizing triples!")
    
    if self.raw_selects == "*":
      self.vars_needed_for_select = { self.parse_var(var_name) for var_name in self.block.get_ordered_vars() }         

    for i, triple in enumerate(self.triples): # Pass 0: Simple union blocks
      if isinstance(triple, UnionBlock) and triple.simple_union_triples:
        self.triples[i:i+1] = triple.simple_union_triples
        
    remnant_triples = set(self.triples)
    
    for triple in list(self.triples): # Pass 1: Determine var type and prop type
      if isinstance(triple, (Bind, Filter, Block)): continue
      triple.local_table_type = triple.table_type
      
      if triple.optional: continue # Optional => cannot be used to restrict variable type
      s, p, o = triple
      if s.name == "VAR":
        var = self.parse_var(s)
        var.update_type("objs")
        if (p.name == "IRI") and (p.storid == rdfs_subpropertyof) and (o.name == "IRI"):
          parent_prop = self.translator.world._get_by_storid(o.storid)
          if   isinstance(parent_prop, ObjectPropertyClass): var.prop_type = "objs"
          elif isinstance(parent_prop, DataPropertyClass):   var.prop_type = "datas"
      if p.name == "VAR": self.parse_var(p).update_type("objs")
      if o.name == "VAR": self.parse_var(o).update_type(triple.local_table_type)
      
    for triple in list(self.triples): # Pass 2: Determine var type, which may be changed due to prop type
      if isinstance(triple, (Bind, Filter, Block)): continue
      s, p, o = triple
      if (triple.local_table_type == "quads") and (o.name == "VAR"): triple.local_table_type = self.parse_var(o).type
      if (triple.local_table_type == "quads") and (p.name == "VAR"): triple.local_table_type = self.parse_var(p).prop_type # Repeat (table.type == "quads") condition, since table.type may have been changed by the previous if block
      if o.name == "VAR": self.parse_var(o).update_type(triple.local_table_type)
      
    non_preliminary_triples = []
    for triple in list(self.triples): # Pass 3: Create recursive preliminary selects
      if isinstance(triple, Block): continue
      if isinstance(triple, (Bind, Filter)):
        non_preliminary_triples.append(triple)
        continue
      s, p, o = triple
      triple.consider_s = triple.consider_p = triple.consider_o = True
      
      if p.modifier:
        if   (s.name != "VAR"): fixed = "s"
        elif (o.name != "VAR"): fixed = "o"
        else:
          fix_levels = self.get_fix_levels([self.parse_var(s), self.parse_var(o)], triple)
          if fix_levels[self.parse_var(s)] >= fix_levels[self.parse_var(o)]: fixed = "s"
          else:                                                              fixed = "o"
          
        non_fixed = "o" if fixed == "s" else "s"
        vars = []
        if   (s.name == "VAR") and (fixed == "s"): fixed_var = s
        elif (o.name == "VAR") and (fixed == "o"): fixed_var = o
        else:                                      fixed_var = None
        if fixed_var: vars.append(self.parse_var(fixed_var))
        if  p.name == "VAR": vars.append(self.parse_var(p))
        
        prelim_triples = self.extract_triples(self.triples, vars, triple)
        
        if triple in remnant_triples: remnant_triples.remove(triple)
        remnant_triples.difference_update(prelim_triples)
        prelim = self.translator.get_recursive_preliminary_select(triple, fixed, fixed_var, prelim_triples)
        triple.local_table_type = prelim.name
        triple.consider_p = False
        if not(fixed_var and prelim_triples):
          if fixed == "s": triple.consider_s = False
          else:            triple.consider_o = False
          
      else:
        non_preliminary_triples.append(triple)
        
    selected_non_preliminary_triples = frozenset(self.extract_triples(non_preliminary_triples, self.vars_needed_for_select))
    selected_non_preliminary_triples = selected_non_preliminary_triples | remnant_triples
    
    
    vars_needing_binding = set(self.vars_needed_for_select)
    for triple in self.triples: # Pass 4: compute number of bindings per variable
      if   isinstance(triple, (Bind, Filter)):
        for var_name in triple.var_names:
          vars_needing_binding.add(self.parse_var(var_name))
        continue
      if   isinstance(triple, Block): continue
      s, p, o = triple
      if (not p.modifier) and (not triple in selected_non_preliminary_triples): continue
      if triple.local_table_type.startswith("prelim") and not triple.consider_p: continue
      for (x, consider) in zip(triple, [triple.consider_s, triple.consider_p, triple.consider_o]):
        if consider and (x.name == "VAR"):
          x = self.parse_var(x)
          x.nb_table += 1
          
    for triple in self.triples: # Pass 5: pre-register bindings for preliminary table
      if   isinstance(triple, (Bind, Filter, Block)): continue
      s, p, o = triple
      if (not p.modifier) and (not triple in selected_non_preliminary_triples): continue
      
      triple.to_skip = False
      if self.raw_selects == "*": continue
      if triple.local_table_type.startswith("prelim") and not triple.consider_p:
        if (s.name == "VAR") and (self.parse_var(s) in vars_needing_binding) and self.parse_var(s).nb_table == 0: continue
        if (o.name == "VAR") and (self.parse_var(o) in vars_needing_binding) and self.parse_var(o).nb_table == 0: continue
        triple.to_skip = True
        extra = ""
        if p.modifier == "+": extra = " WHERE nb>0"
        if s.name == "VAR":
          s = self.parse_var(s)
          s.bindings.insert(0, """IN (SELECT s FROM %s%s)""" % (triple.local_table_type, extra))
        if o.name == "VAR":
          o = self.parse_var(o)
          o.bindings.insert(0, """IN (SELECT o FROM %s%s)""" % (triple.local_table_type, extra))

    has_optional_triple = False
    for triple in self.triples:
      if getattr(triple, "optional", False):
        has_optional_triple = True
        break
        
    conditions = self.conditions
    if isinstance(triples, TripleBlockWithStatic):
      for static in triples.static_valuess:
        if isinstance(static, StaticBlock):
          if self.raw_selects == "*":
            static.vars = sorted(static.all_vars)
          else:
            used_vars = set(self.vars)
            used_vars.update(var.name for var in self.vars_needed_for_select)
            static.vars = sorted(var for var in static.all_vars if (var in used_vars))
            
          for var in static.vars:
            var = static.translator.main_query.vars.get(var)
            if var: static.types.append(var.type)
            else:   static.types.append("quads")
              
          var_2_columns = defaultdict(list)
          for column in static.translator.main_query.columns:
            var_2_columns[column.var].append(column)
            
          static.translator.main_query.raw_selects = static.vars
          static.translator.main_query.columns = []
          static.translator.main_query.finalize_columns()
          static.translator.solution_modifier = [None, None, None, None, None]
          q = static.translator.finalize()
          static.valuess = list(q._execute_sql())
          
        if (not has_optional_triple) and len(static.vars) == 1: # This optimization is not supported with optional blocks
          var = self.parse_var(static.vars[0])
          var.update_type(static.types[0])
          sql, sql_type, sql_d, sql_d_type = self._to_sql(var)
          if sql is None:
            var.bindings.append("IN (%s)" % ",".join(str(value[0]) for value in static.valuess))
            var.static = static.valuess
            var.type = "objs"
          else:
            conditions.append("%s IN (%s)" % (sql, ",".join(str(value[0]) for value in static.valuess)))
            
        else:
          prelim = SQLStaticValuesPreliminaryQuery(self.translator, "static%s" % (len(self.translator.preliminary_selects) + 1), static)
          self.translator.preliminary_selects.append(prelim)
          table = Table(self, prelim.name, prelim.name)
          for i, (var, type) in enumerate(zip(static.vars, static.types)):
            var = self.parse_var(var)
            var.update_type(type)
            sql, sql_type, sql_d, sql_d_type = self._to_sql(var)
            if sql is None:
              var.bindings.append("%s.col%s_o" % (prelim.name, i + 1))
            else:
              var.bindings.insert(0, "%s.col%s_o" % (prelim.name, i + 1)) # Favor static binding, because it is never optional
              conditions.append("%s=%s.col%s_o" % (sql, prelim.name, i + 1))
    
    for triple in self.triples: # Pass 6: create triples tables and conditions
      if   isinstance(triple, Bind):
        self.parse_bind(triple)
        continue
      elif isinstance(triple, Filter):
        self.parse_filter(triple)
        continue
      elif isinstance(triple, Block):
        if   isinstance(triple, SimpleTripleBlock) and (len(triple) == 0): continue # Empty
        elif isinstance(triple, FilterBlock):
          sub = self.translator.new_sql_query(None, triple, nested_inside = self)
          self.add_subquery(sub)
          continue
        else:
          sub = self.translator.new_sql_query(None, triple, preliminary = True, nested_inside = self, copy_vars = True)
          self.add_subquery(sub)
          continue
      if triple.to_skip: continue
      
      s, p, o = triple
      if (not p.modifier) and (not triple in selected_non_preliminary_triples): continue
      
      if self.name == "main": select_name = ""
      else:                   select_name = "%s_" % (self.name or "")
      table = Table(self, "%sq%s" % (select_name, self.translator.next_table_id), triple.local_table_type)
      if triple.optional:
        table.join = "LEFT JOIN"
        conditions = table.join_conditions
      else:
        conditions = self.conditions
      self.translator.next_table_id += 1
      
      if triple.consider_s: self.create_conditions(conditions, table, "s", s)
      if triple.consider_p: self.create_conditions(conditions, table, "p", p, triple.likelihood_p)
      if triple.consider_o: self.create_conditions(conditions, table, "o", o, triple.likelihood_o)
      
      if p.modifier == "+": conditions.append("%s.nb>0"  % table.name)
      
    # if isinstance(triples, TripleBlockWithStatic):
    #   for static in triples.static_valuess:
    #     if isinstance(static, StaticBlock):
    #       if self.raw_selects == "*":
    #         static.vars = sorted(static.all_vars)
    #       else:
    #         used_vars = set(self.vars)
    #         used_vars.update(var.name for var in self.vars_needed_for_select)
    #         static.vars = sorted(var for var in static.all_vars if (var in used_vars))
            
    #       for var in static.vars:
    #         var = static.translator.main_query.vars.get(var)
    #         if var: static.types.append(var.type)
    #         else:   static.types.append("quads")
              
    #       var_2_columns = defaultdict(list)
    #       for column in static.translator.main_query.columns:
    #         var_2_columns[column.var].append(column)
            
    #       static.translator.main_query.raw_selects = static.vars
    #       static.translator.main_query.columns = []
    #       static.translator.main_query.finalize_columns()
    #       static.translator.solution_modifier = [None, None, None, None, None]
    #       q = static.translator.finalize()
    #       static.valuess = list(q._execute_sql())
          
    #     if (not [table for table in self.tables if table.join != ","]) and len(static.vars) == 1: # This optimization is not supported with optional blocks
    #       var = self.parse_var(static.vars[0])
    #       var.update_type(static.types[0])
    #       sql, sql_type, sql_d, sql_d_type = self._to_sql(var)
    #       if sql is None:
    #         var.bindings.append("IN (%s)" % ",".join(str(value[0]) for value in static.valuess))
    #         var.static = static.valuess
    #         var.type = "objs"
    #       else:
    #         conditions.append("%s IN (%s)" % (sql, ",".join(str(value[0]) for value in static.valuess)))
            
    #     else:
    #       prelim = SQLStaticValuesPreliminaryQuery(self.translator, "static%s" % (len(self.translator.preliminary_selects) + 1), static)
    #       self.translator.preliminary_selects.append(prelim)
    #       table = Table(self, prelim.name, prelim.name)
    #       for i, (var, type) in enumerate(zip(static.vars, static.types)):
    #         var = self.parse_var(var)
    #         var.update_type(type)
    #         sql, sql_type, sql_d, sql_d_type = self._to_sql(var)
    #         if sql is None:
    #           var.bindings.append("%s.col%s_o" % (prelim.name, i + 1))
    #         else:
    #           var.bindings.insert(0, "%s.col%s_o" % (prelim.name, i + 1)) # Favor static binding, because it is never optional
    #           conditions.append("%s=%s.col%s_o" % (sql, prelim.name, i + 1))
              
              
  def get_fix_levels(self, vars0, exclude_triple = None):
    vars0_names = { var.name for var in vars0 }
    fix_levels  = defaultdict(float)
    fix_triples = {}
    
    def fix(var, triple, via_vars, w = 1.0):
      nonlocal changed
      
      w0 = min((0.5 * fix_levels[via_var] for via_var in via_vars), default = 1.0)
      w  = w * w0
      
      if w > fix_levels[var]:
        changed          = True
        fix_levels [var] = w
        fix_triples[var] = l = { triple }
        for via_var in via_vars: l.update(fix_triples[via_var])
        
    def scan_triple(triples, w = 1):
      for triple in self.triples:
        if triple is exclude_triple: continue
        
        if   isinstance(triple, Triple):
          if   len(triple.var_names) == 1:
            var = self.parse_var(tuple(triple.var_names)[0])
            fix(var, triple, [], w)
            
          elif len(triple.var_names) == 2:
            if triple.var_names != vars0_names:
              vars = [self.parse_var(var_name) for var_name in triple.var_names]
              for v1, v2 in [(vars[0], vars[1]), (vars[1], vars[0])]:
                fix(v1, triple, [v2], w)
                
        elif isinstance(triple, Filter):
          pass
        elif isinstance(triple, Bind):
          var = self.parse_var(triple.var)
          fix(var, triple, [self.parse_var(var_name) for var_name in triple.var_names], w)
          
        elif isinstance(triple, UnionBlock):
          for alternative in triple: scan_triple(alternative, w / len(triple))
          
    while True:
      changed = False
      scan_triple(self.triples)
      if not changed: break
      for var in vars0:
        if not var in fix_levels: break
      else:
        break
      
    return fix_levels
      
  def extract_triples(self, triples, vars, except_triple = None):
    var_names = { var.name for var in vars }
    while True:
      r = [triple for triple in triples if (not triple == except_triple) and isinstance(triple, (Triple, Filter, Bind)) and (not triple.var_names.isdisjoint(var_names))]
      var_names2 = { var_name for triple in r for var_name in triple.var_names }
      if var_names2 == var_names:
        return r
      var_names = var_names2
      
  def create_conditions(self, conditions, table, n, x, likelihood = None):
    if isinstance(x, SpecialCondition):
      x.create_conditions(conditions, table, n)
    else:
      sql, sql_type, sql_d, sql_d_type = self._to_sql(x)
      
      if table.subquery: # If datatype is 0 (=auto), disable datatype conditions and replace it by IS NOT NULL
        for column in table.subquery.columns:
          if column.name == "%sd" % n[:-1]:
            if str(column.binding) == "0":
              sql_d = None
              conditions.append("%s.%sd IS NOT NULL" % (table.name, n[:-1])) # Datatype part
            break
          
          
      if not sql is None:
        if isinstance(sql, str) and sql.startswith("IN "): operator = " "; sqls = self.parse_var(x).bindings
        else:                                              operator = "="; sqls = [sql]
        
        for sql in sqls:
          condition = "%s.%s%s%s"  % (table.name, n, operator, sql)
          if likelihood is None: conditions.append(condition)
          else:                  conditions.append("LIKELIHOOD(%s, %s)" % (condition, likelihood))
          
      if (not sql_d is None) and (sql_d != 0) and (n != "s") and (n != "p") and (table.name != "objs"):
        conditions.append("%s.%sd=%s" % (table.name, n[:-1], sql_d)) # Datatype part
        
      if isinstance(x, rply.Token) and (x.name == "VAR"): x = self.vars[x.value]
      if isinstance(x, Variable):
        if not x.initial_query: x.initial_query = self
        x.bindings.append("%s.%s" % (table.name, n))
    
  def try_create_in_conditions(self, conditions, x, prelim):
    if prelim.optional or (len(prelim.columns) != 1) or (x is None): return False

    assert len(prelim.columns) == 1
    if isinstance(x, rply.Token):
      assert x.name == "VAR"
      x_varname = x.value
    else:
      x_varname = x
      
    for triple in self.triples: # Verify if the variable is used outside the prelim query -- otherwise, the IN optimization cannot be used
      if isinstance(triple, Triple):
        if isinstance(triple[0], rply.Token) and (triple[0].name == "VAR") and (triple[0].value == x_varname): break
        if isinstance(triple[1], rply.Token) and (triple[1].name == "VAR") and (triple[1].value == x_varname): break
        if isinstance(triple[2], rply.Token) and (triple[2].name == "VAR") and (triple[2].value == x_varname): break
    else:
      return False
    
    column = prelim.columns[0]
    var = self.parse_var(x)
    sql, sql_type, sql_d, sql_d_type = self._to_sql(var)
    if sql is None:
      var.bindings.append("IN (SELECT %s FROM %s)" % (column.name, prelim.name))
      var.update_type(column.type)
      var.in_select = prelim
    else:
      conditions.append("%s IN (SELECT %s FROM %s)" % (sql, column.name, prelim.name))
    return True  
      
  def is_fixed(self, x):
    if x.name != "VAR": return True
    x = self.parse_var(x)
    if x.initial_query and (x.initial_query is not self): return True
    if x.bindings: return True
    return False
  
  def finalize_columns(self):
    selected_parameter_index = 0
    i = j = 0
    
    if   self.raw_selects == "*": selects = [self.vars[var] for var in self.block.get_ordered_vars() if not var.startswith("??")]      
    elif self.raw_selects:        selects = self.raw_selects
    elif self.tables:
      if self.tables[0].type in { "objs", "datas", "quads" }:
                                  selects = ["1"] # Nothing to select (see TestSPARQL.test_128)
      else:                       selects = ["%s.%s" % (self.tables[0].name, col) for col in self.translator.table_type_2_cols[self.tables[0].type]]
    else:                         selects = []
    
    def do_select(select):
      nonlocal selected_parameter_index
      if isinstance(select, str) and select.startswith("?"): select = self.vars[select]
      sql, sql_type, sql_d, sql_d_type = self._to_sql(select)

      if   isinstance(select, rply.Token) and (select.name == "VAR"): var_name = select.value
      elif isinstance(select, Variable):                              var_name = select.name
      else:                                                           var_name = None
      
      if sql == "?":
        self.parameters.insert(selected_parameter_index, select.number)
        selected_parameter_index += 1

      return var_name, sql, sql_type, sql_d, sql_d_type
    
    for select in selects:
      i += 1
      if isinstance(select, SimpleUnion):
        self.select_simple_union = True
        sql = []
        for select_item in select.items:
          var_name, sql_i, sql_type, sql_d, sql_d_type = do_select(select_item)
          sql.append(sql_i)
        sql_d = None # SimpleUnion is only supported for object here
        
      else:
        var_name, sql, sql_type, sql_d, sql_d_type = do_select(select)
        
      if sql is None:
        if not self.name: # Inside a UNION => the variable is not available in this alternative of th UNION
          sql = "NULL"
          sql_type = "objs"
        else:
          raise ValueError("Cannot select '%s'!" % select)
        
      if isinstance(sql, str) and sql.startswith("IN "):
        if   not "," in sql: sql = sql[4 : -1]
        elif len(selects) == 1: pass # Ok
        else:
          raise ValueError("Cannot SELECT a variable that appears only in a VALUES clause with multiple values (not yet supported).")
        
      self.columns.append(Column(var_name, sql_type, sql, "col%s_o" % i, j)); j += 1
      if not sql_d is None:
        self.columns.append(Column(var_name, sql_d_type, sql_d, "col%s_d" % i, j)); j += 1

    if self.preliminary:
      self.translator.table_type_2_cols[self.name] = [column.name for column in self.columns]

    
  def set_column_names(self, names):
    for column, name in zip(self.columns, names): column.name = name
    
    if self.preliminary:
      self.translator.table_type_2_cols[self.name] = names
      
  def _to_sql(self, x):
    if isinstance(x, rply.Token) and (x.name == "VAR"): x = self.parse_var(x)

    if   isinstance(x, str): return x, "value", None, None
    elif isinstance(x, Variable):
      if not x.bindings: return None, None, None, None
      binding = x.get_binding(self)
      if   x.type == "objs":  return binding, "objs", None, None
      else:
        if not x.fixed_datatype is None:
          if isinstance(x.fixed_datatype, Variable):
            dropit, dropit, other_sql_d, other_sql_d_type = self._to_sql(x.fixed_datatype)
            return binding, "datas", other_sql_d, other_sql_d_type
          else:
            return binding, "datas", x.fixed_datatype, "datas"
        type = "datas" if x.type == "datas" else "quads"
        if binding.startswith("static"): # no 'd' for static yet
          return binding, type, 0, type
        else:
          return binding, type, "%sd" % binding[:-1], type
    elif x.name == "IRI":   return x.storid, "objs", None, None
    elif x.name == "PARAM": return "?%s" % x.number, "objs", None, None # XXX data parameter
    else:
      if   x.name == "DATA":            return x.value, "value", x.datatype, "value"
      elif isinstance(x.value, locstr): return x.value, "value", "'@%s'" % x.value.lang, "value"
      else:                             return x.value, "value", None, None
      
    
class SQLCompoundQuery(object):
  recursive = False
  def __init__(self, name, parent):
    self.name                    = name
    self.parent                  = parent
    self.translator              = CURRENT_TRANSLATOR.get()
    self.queries                 = []
    self.preliminary             = False
    self.optional                = False
    
  def __repr__(self): return "<%s '%s'>" % (self.__class__.__name__, self.sql())
  
  def append(self, query, operator = ""):
    query.operator = operator
    self.queries.append(query)
    
  def sql(self):
    sql = ""
    for i, query in enumerate(self.queries):
      if i != 0: sql += "\n%s\n" % query.operator
      sql += query.sql()
      
    if self.preliminary: return """%s(%s) AS (%s)""" % (self.name, ", ".join(column.name for column in self.columns), sql)
    return sql
  
  def finalize_compounds(self):
    has_d = set()
    for query in self.queries:
      for column in query.columns:
        if column.name.endswith("d"):
          has_d.add(column.name.split("_", 1)[0])
          
    for query in self.queries:
      for i, column in enumerate(query.columns):
        if column.name.endswith("o") and (column.name.split("_", 1)[0] in has_d):
          column.type = "quads"
          if (column is query.columns[-1]) or (not query.columns[i+1].name.endswith("d")):
            query.columns.insert(i + 1, Column(column.var, "quads", "NULL", "%sd" % column.name[:-1], i + 1))
      for i, column in enumerate(query.columns): # Re-index columns
        column.index = i
    self.columns = self.queries[0].columns
    
    self.translator.table_type_2_cols[self.name] = [column.name for column in self.columns]
    
    
class SQLNestedQuery(SQLQuery):
  def __init__(self, name):
    SQLQuery.__init__(self, name)
    self.exists = True
    
  def finalize_columns(self):
    self.columns = [Column(None, "datas", "1", "col1_o", 1)]
    
  #def sql(self):
  #  return "SELECT WHERE %s" % self.nested_sql()
  
  def nested_sql(self):
    sql = SQLQuery.sql(self)
    
    if _DEPRIORIZE_SUBQUERIES_OPT:
      if   self.exists == True:  sql =     "one.i= EXISTS(%s)" % sql
      elif self.exists == False: sql = "NOT one.i= EXISTS(%s)" % sql
      else:                      sql = "(%s)" % sql
    else:
      if   self.exists == True:  sql =     "EXISTS(%s)" % sql
      elif self.exists == False: sql = "NOT EXISTS(%s)" % sql
      else:                      sql = "(%s)" % sql

    return sql
  
  def __str__(self): return self.nested_sql()
  

class SQLRecursivePreliminaryQuery(SQLQuery):
  def __init__(self, name, triple, fixed, fixed_var):
    s, p, o = triple
    translator = CURRENT_TRANSLATOR.get()
    self.fixed        = fixed
    self.fixed_var    = fixed_var
    self.non_fixed    = "o" if fixed == "s" else "s"
    
    if isinstance(p, NegatedPropPath): self.need_d = True
    else:                              self.need_d = (p.modifier == "?") and not isinstance(triple.Prop, ObjectPropertyClass)
    
    self.need_orig    = not self.fixed_var is None # XXX Optimizable
    self.need_nb      = p.modifier != "*"
    
    SQLQuery.__init__(self, "%s_%s" % (name, "quads" if self.need_d else "objs"))
    self.recursive    = True
    self.preliminary  = True
    
  def build(self, triple, prelim_triples):
    s, p, o = triple
    column_names = [self.non_fixed] + ["d"] * self.need_d + [self.fixed] * self.need_orig + ["nb"] * self.need_nb
    if self.fixed_var and prelim_triples: value = self.fixed_var
    else:                                 value = s if self.fixed == "s" else o
    self.parse_selects([value] + ["NULL"] * self.need_d + [value] * self.need_orig + ["0"] * self.need_nb)
    self.parse_triples(prelim_triples)
    self.finalize_columns()
    self.set_column_names(column_names)
    
    p_direct_conditions   = []
    p_inversed_conditions = []
    if isinstance(p, UnionPropPath):
      direct_ps   = [i for i in p if not i.inversed]
      inversed_ps = [i for i in p if     i.inversed]
      if direct_ps:
        if len(direct_ps) == 1:
          self.create_conditions(p_direct_conditions, Table(None, "q", "quads" if self.need_d else "objs"), "p", direct_ps[0])
        else:
          p_direct_conditions  .append("q.p IN (%s)" % ",".join(str(self._to_sql(i)[0]) for i in direct_ps))
          
      if inversed_ps:
        if len(inversed_ps) == 1:
          self.create_conditions(p_inversed_conditions, Table(None, "q", "quads" if self.need_d else "objs"), "p", inversed_ps[0])
        else:
          p_inversed_conditions.append("q.p IN (%s)" % ",".join(str(self._to_sql(i)[0]) for i in inversed_ps))
          
    else:
      self.create_conditions(p_direct_conditions, Table(None, "q", "quads" if self.need_d else "objs"), "p", p)
      
    self.extra_sql = ""
    if p_direct_conditions:
      self.extra_sql += """
UNION
SELECT q.%s%s%s%s FROM %s q, %s rec WHERE %s %sAND q.%s=rec.%s""" % (
  self.non_fixed,
  ", q.d"                 if self.need_d    else "",
  ", rec.%s" % self.fixed if self.need_orig else "",
  ", rec.nb+1"            if self.need_nb   else "",
  "quads"                 if self.need_d    else "objs",
  self.name, " AND ".join(p_direct_conditions),
  "AND rec.nb=0 " if p.modifier == "?" else "",
  self.fixed, self.non_fixed)
  
    if p_inversed_conditions:
      self.extra_sql += """
UNION
SELECT q.%s%s%s%s FROM %s q, %s rec WHERE %s %sAND q.%s=rec.%s""" % (
  self.fixed,
  ", q.d"                     if self.need_d    else "",
  ", rec.%s" % self.non_fixed if self.need_orig else "",
  ", rec.nb+1"                if self.need_nb   else "",
  "quads"                     if self.need_d    else "objs",
  self.name, " AND ".join(p_inversed_conditions),
  "AND rec.nb=0 " if p.modifier == "?" else "",
  self.non_fixed, self.non_fixed)

    
      
class SQLStaticValuesPreliminaryQuery(object):
  recursive = False
  def __init__(self, translator, name, static_values):
    self.translator    = translator
    self.name          = name
    self.static_values = static_values
    
    if self.static_values.valuess:
      self.nb_value = len(self.static_values.valuess[0])
    else:
      raise ValueError("VALUES clause cannot be empty (this also applies to STATIC block returning no results)!")
    self.translator.table_type_2_cols[self.name] = ["col%s_o" % (i+1) for i in range(self.nb_value)]
    
    self.columns = []
    for i in range(self.nb_value):
      self.columns.append(Column(static_values.vars[i], "objs", "xxx", "col%s_o" % (i+1), i))
      
  def sql(self):
    return "%s(%s) AS (VALUES %s)" % (self.name,
                                      ",".join("col%s_o" % (i+1) for i in range(self.nb_value)),
                                      ",".join("(%s)" % ",".join(str(value) for value in values) for values in self.static_values.valuess) )

