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


import sys, os, re
import owlready2.rply as rply
from owlready2.util import ContextVar
from owlready2 import *
from owlready2.base import _universal_abbrev_2_datatype_parser

lg = rply.LexerGenerator()
lg.add("}",                    r"\}")
lg.add("{",                    r"\{")
lg.add("NIL",                  r"\(\s*\)")
lg.add("ANON",                 r"\[\s*\]")
lg.add(")",                    r"\)")
lg.add("(",                    r"\(")
lg.add("[",                    r"\[")
lg.add("]",                    r"\]")
lg.add("DOUBLE",               r"""[+-]?[0-9]*\.[0-9]+[eE][+-]?[0-9]+""")
lg.add("DOUBLE",               r"""[+-]?[0-9]+[eE][+-]?[0-9]+""")
lg.add("DECIMAL",              r"""[+-]?[0-9]*\.[0-9]+""")
lg.add("INTEGER",              r"""[+-]?[0-9]+""")
lg.add("-",                    r"-")
lg.add("+",                    r"\+")
lg.add("*STATIC",              r"\*STATIC")
lg.add("*",                    r"\*")
lg.add("/",                    r"/")
lg.add(",",                    r",")
lg.add(";",                    r";")
lg.add("=",                    r"=")
lg.add("&&",                   r"&&")
lg.add("||",                   r"\|\|")
lg.add("|",                    r"\|")
lg.add("VAR",                  r"""(?:\?|\$)\w+""")
lg.add("IRI",                  r"""<([^<>\s])+>""")
lg.add("LANG_TAG",             r"""@[a-zA-Z]+(-[a-zA-Z0-9]+)*""")
lg.add("BOOL",                 r"""(?:true)|(?:false)\b""", re.IGNORECASE)
lg.add("BLANK_NODE_LABEL",     r"""_:[\w\.\-]*""")
lg.add("^^",                   r"""\^\^""")
lg.add("^",                    r"""\^""")
lg.add("PARAM",                r"""\?\?[0-9]*""")
lg.add("?",                    r"""\?""")
lg.add(".",                    r"""\.""")
lg.add("PREFIXED_NAME",        r"""[\w\.\-]*:([\w\.\-:]|%[0-9a-fA-F]{2}|\\[_~\.\-!$&"'()*+,;=/?#@%])*([\w\-:]|%[0-9a-fA-F]{2}|\\[_~\.\-!$&"'()*+,;=/?#@%])""")
lg.add("PNAME_NS",             r"""[\w\.\-]*:""")
lg.add("FUNC",                 r"""(?:STRLANG)|(?:STRDT)|(?:STRLEN)|(?:STRSTARTS)|(?:STRENDS)|(?:STRBEFORE)|(?:STRAFTER)|(?:LANGMATCHES)|(?:LANG)|(?:DATATYPE)|(?:BOUND)|(?:IRI)|(?:URI)|(?:BNODE)|(?:RAND)|(?:ABS)|(?:CEIL)|(?:FLOOR)|(?:ROUND)|(?:CONCAT)|(?:STR)|(?:UCASE)|(?:LCASE)|(?:ENCODE_FOR_URI)|(?:CONTAINS)|(?:YEAR)|(?:MONTH)|(?:DAY)|(?:HOURS)|(?:MINUTES)|(?:SECONDS)|(?:TIMEZONE)|(?:TZ)|(?:NOW)|(?:UUID)|(?:STRUUID)|(?:MD5)|(?:SHA1)|(?:SHA256)|(?:SHA384)|(?:SHA512)|(?:COALESCE)|(?:IF)|(?:sameTerm)|(?:isIRI)|(?:isURI)|(?:isBLANK)|(?:isLITERAL)|(?:isNUMERIC)|(?:REGEX)|(?:SUBSTR)|(?:REPLACE)|(?:SIMPLEREPLACE)|(?:NEWINSTANCEIRI)|(?:LOADED)|(?:STORID)|(?:DATETIME_DIFF)|(?:DATETIME_ADD)|(?:DATETIME_SUB)|(?:DATETIME)|(?:DATE_ADD)|(?:DATE_DIFF)|(?:DATE_SUB)|(?:DATE)|(?:TIME)\b""", re.IGNORECASE)
#lg.add("FUNC",                 r"""(?:STRLANG)|(?:STRDT)|(?:STRLEN)|(?:STRSTARTS)|(?:STRENDS)|(?:STRBEFORE)|(?:STRAFTER)|(?:LANGMATCHES)|(?:LANG)|(?:DATATYPE)|(?:BOUND)|(?:IRI)|(?:URI)|(?:BNODE)|(?:RAND)|(?:ABS)|(?:CEIL)|(?:FLOOR)|(?:ROUND)|(?:CONCAT)|(?:STR)|(?:UCASE)|(?:LCASE)|(?:ENCODE_FOR_URI)|(?:CONTAINS)|(?:YEAR)|(?:MONTH)|(?:DAY)|(?:HOURS)|(?:MINUTES)|(?:SECONDS)|(?:TIMEZONE)|(?:TZ)|(?:NOW)|(?:UUID)|(?:STRUUID)|(?:MD5)|(?:SHA1)|(?:SHA256)|(?:SHA384)|(?:SHA512)|(?:COALESCE)|(?:IF)|(?:sameTerm)|(?:isIRI)|(?:isURI)|(?:isBLANK)|(?:isLITERAL)|(?:isNUMERIC)|(?:REGEX)|(?:SUBSTR)|(?:REPLACE)|(?:SIMPLEREPLACE)|(?:NEWINSTANCEIRI)|(?:XSD:DOUBLE)|(?:XSD:INTEGER)\b""", re.IGNORECASE)
lg.add("MINUS",                r"""MINUS\b""", re.IGNORECASE)
lg.add("AGGREGATE_FUNC",       r"""(?:COUNT)|(?:SUM)|(?:MIN)|(?:MAX)|(?:AVG)|(?:SAMPLE)|(?:GROUP_CONCAT)\b""", re.IGNORECASE)
lg.add("BASE",                 r"""BASE\b""", re.IGNORECASE)
lg.add("PREFIX",               r"""PREFIX\b""", re.IGNORECASE)
lg.add("SELECT",               r"""SELECT\b""", re.IGNORECASE)
lg.add("DISTINCT",             r"""DISTINCT\b""", re.IGNORECASE)
lg.add("REDUCED",              r"""REDUCED\b""", re.IGNORECASE)
lg.add("EXISTS",               r"""EXISTS\b""", re.IGNORECASE)
lg.add("NOT_EXISTS",           r"""NOT\s+EXISTS\b""", re.IGNORECASE)
lg.add("FILTER",               r"""FILTER\b""", re.IGNORECASE)
lg.add("UNION",                r"""UNION\b""", re.IGNORECASE)
lg.add("UNDEF",                r"""UNDEF\b""", re.IGNORECASE)
lg.add("VALUES",               r"""VALUES\b""", re.IGNORECASE)
lg.add("BIND",                 r"""BIND\b""", re.IGNORECASE)
lg.add("WITH",                 r"""WITH\b""", re.IGNORECASE)
lg.add("AS",                   r"""AS\b""", re.IGNORECASE)
lg.add("WHERE",                r"""WHERE\b""", re.IGNORECASE)
lg.add("OPTIONAL",             r"""OPTIONAL\b""", re.IGNORECASE)
#lg.add("GRAPH",                r"""GRAPH\b""", re.IGNORECASE)
#lg.add("SERVICE",              r"""SERVICE\b""", re.IGNORECASE)
#lg.add("SILENT",               r"""SILENT\b""", re.IGNORECASE)
#lg.add("DEFAULT",              r"""DEFAULT\b""", re.IGNORECASE)
lg.add("NAMED",                r"""NAMED\b""", re.IGNORECASE)
#lg.add("ALL",                  r"""ALL\b""", re.IGNORECASE)
lg.add("USING",                r"""USING\b""", re.IGNORECASE)
lg.add("INSERT",               r"""INSERT\b""", re.IGNORECASE)
lg.add("DELETE",               r"""DELETE\b""", re.IGNORECASE)
#lg.add("DATA",                 r"""DATA\b""", re.IGNORECASE)
lg.add("SEPARATOR",            r"""SEPARATOR\b""", re.IGNORECASE)
#lg.add("CLEAR",                r"""CLEAR\b""", re.IGNORECASE)
#lg.add("INTO",                 r"""INTO\b""", re.IGNORECASE)
#lg.add("TO",                   r"""TO\b""", re.IGNORECASE)
#lg.add("LOAD",                 r"""LOAD\b""", re.IGNORECASE)
#lg.add("DROP",                 r"""DROP\b""", re.IGNORECASE)
#lg.add("CREATE",               r"""CREATE\b""", re.IGNORECASE)
#lg.add("ADD",                  r"""ADD\b""", re.IGNORECASE)
#lg.add("MOVE",                 r"""MOVE\b""", re.IGNORECASE)
#lg.add("COPY",                 r"""COPY\b""", re.IGNORECASE)
lg.add("HAVING",               r"""HAVING\b""", re.IGNORECASE)
lg.add("ORDER_BY",             r"""ORDER\s+BY\b""", re.IGNORECASE)
lg.add("GROUP_BY",             r"""GROUP\s+BY\b""", re.IGNORECASE)
lg.add("FROM",                 r"""FROM\b""", re.IGNORECASE)
lg.add("ASC",                  r"""ASC\b""", re.IGNORECASE)
lg.add("DESC",                 r"""DESC\b""", re.IGNORECASE)
lg.add("LIMIT",                r"""LIMIT\b""", re.IGNORECASE)
lg.add("OFFSET",               r"""OFFSET\b""", re.IGNORECASE)
lg.add("STATIC",               r"STATIC")
#lg.add("DESCRIBE",             r"""DESCRIBE\b""", re.IGNORECASE)
#lg.add("ASK",                  r"""ASK\b""", re.IGNORECASE)
#lg.add("CONSTRUCT",            r"""CONSTRUCT\b""", re.IGNORECASE)
lg.add("COMPARATOR",           r"""(?:\!=)|(?:<=)|(?:>=)|(?:<)|(?:>)""")
lg.add("!",                    r"\!")
lg.add("LIST_COMPARATOR",      r"""(?:IN)|(?:NOT\s+IN)\b""", re.IGNORECASE)
lg.add("A",                    r"""a\b""")
lg.add("STRING_LITERAL1",      r"""'(?:[^'\n\r\\]|\\['ntbrf\\])*'(?!')""")
lg.add("STRING_LITERAL2",      r'''"(?:[^"\n\r\\]|\\["ntbrf\\])*"(?!")''')
lg.add("STRING_LITERAL_LONG1", r"""'''.*?'''""")
lg.add("STRING_LITERAL_LONG2", r'''""".*?"""''')

lg.ignore(r"\s+")
lg.ignore(r"#.*?\n|$")

LEXER = lg.build()
pg = rply.ParserGenerator([rule.name for rule in lg.rules])

@pg.production("main : prefix_decl* select_query")
#@pg.production("main : prefix_decl* construct_query values_clause?")
#@pg.production("main : prefix_decl* describe_query values_clause?")
#@pg.production("main : prefix_decl* ask_query values_clause?")
def f(p): return _parse_select_query(p[1])

def _parse_select_query(p):
  translator = CURRENT_TRANSLATOR.get()
  if isinstance(p[2], rply.Token) and (p[2].value == "*"): p[2] = None
  if isinstance(p[4], UnionBlock) and (p[5][0] or p[5][1] or p[5][2] or p[5][3] or p[5][4]): # UNION with some solution modifier
    p[4] = SimpleTripleBlock([p[4]])
  if isinstance(p[4], NotExistsBlock): # FILTER NOT EXISTS alone; not supported as the main query.
    p[4] = SimpleTripleBlock([p[4]])
  main_query = translator.new_sql_query("main", p[4], p[2], p[1], p[5])
  main_query.type = "select"
  return main_query

#@pg.production("main : prefix_decl* update1+ ;?")
@pg.production("main : prefix_decl* modify")
def f(p): return p[1]
#pg.optional(";?")

@pg.production("prefix_decl : PREFIX PNAME_NS unabbreviated_iri")
def f(p):
  CURRENT_TRANSLATOR.get().prefixes[p[1].value] = p[2].value
  return None
@pg.production("prefix_decl : BASE iri")
def f(p):
  CURRENT_TRANSLATOR.get().base = p[1].value
  return None
pg.list("prefix_decl*", "")

pg.optional("WHERE?")

#@pg.production("select_query : SELECT distinct_reduced? select_clause_part+ WHERE? group_graph_pattern solution_modifier values_clause?")
#@pg.production("select_query : SELECT distinct_reduced? * WHERE? group_graph_pattern solution_modifier values_clause?")
@pg.production("select_query : SELECT distinct_reduced? select_clause_part+ WHERE? group_graph_pattern solution_modifier")
@pg.production("select_query : SELECT distinct_reduced? * WHERE? group_graph_pattern solution_modifier")
def f(p): return p

@pg.production("distinct_reduced? : DISTINCT")
@pg.production("distinct_reduced? : REDUCED")
def f(p): return p[0]
@pg.production("distinct_reduced? : ")
def f(p): return None
@pg.production("select_clause_part : var")
def f(p): return p[0]
@pg.production("select_clause_part : ( expression AS var )")
def f(p): return p[1:-1]
pg.list("select_clause_part+", "")

#@pg.production("construct_query : CONSTRUCT construct_template dataset_clause* WHERE? group_graph_pattern solution_modifier")
#@pg.production("construct_query : CONSTRUCT dataset_clause* WHERE? { triples_template? } solution_modifier")
#def f(p): return p

#@pg.production("describe_query : DESCRIBE var_or_iri+ dataset_clause* where_clause? solution_modifier")
#@pg.production("describe_query : DESCRIBE * dataset_clause* where_clause? solution_modifier")
#def f(p): return p

#@pg.production("ask_query : ASK dataset_clause* WHERE? group_graph_pattern solution_modifier")
#def f(p): return p

@pg.production("dataset_clause : FROM iri")
@pg.production("dataset_clause : FROM NAMED iri")
def f(p): return p
pg.list("dataset_clause*", "")

#@pg.production("where_clause : WHERE? group_graph_pattern")
#def f(p): return p
#pg.optional("where_clause?")

@pg.production("solution_modifier : group_clause? having_clause? order_clause? limit_offset_clauses?")
def f(p):
  if not p[3]: return [p[0], p[1], p[2], None, None]
  return [p[0], p[1], p[2], *p[3]]

@pg.production("group_clause : GROUP_BY group_condition+")
def f(p): return p[1]
pg.optional("group_clause?")

@pg.production("group_condition : builtin_call")
@pg.production("group_condition : function_call")
@pg.production("group_condition : var")
@pg.production("group_condition : expression")
@pg.production("group_condition : expression AS var")
def f(p): return p[0]
pg.list("group_condition+", "")

@pg.production("having_clause : HAVING constraint+")
def f(p): return p[1]
pg.optional("having_clause?")

@pg.production("order_clause : ORDER_BY order_condition+")
def f(p): return p[1]
pg.optional("order_clause?")

@pg.production("order_condition : ASC bracketted_expression")
@pg.production("order_condition : DESC bracketted_expression")
@pg.production("order_condition : constraint")
@pg.production("order_condition : var")
def f(p): return p
pg.list("order_condition+", "")

@pg.production("limit_offset_clauses : limit_clause")
def f(p): return [p[0], None]
@pg.production("limit_offset_clauses : offset_clause")
def f(p): return [None, p[0]]
@pg.production("limit_offset_clauses : limit_clause offset_clause")
def f(p): return p
@pg.production("limit_offset_clauses : offset_clause limit_clause")
def f(p): return [p[1], p[0]]
pg.optional("limit_offset_clauses?")

@pg.production("limit_clause : LIMIT INTEGER")
@pg.production("limit_clause : LIMIT param")
def f(p): return p[1]

@pg.production("offset_clause : OFFSET INTEGER")
@pg.production("offset_clause : OFFSET param")
def f(p): return p[1]

#@pg.production("values_clause : VALUES data_block")
#def f(p): return p
#pg.optional("values_clause?")
#def f(p): return p

#@pg.production("update1 : load")
#@pg.production("update1 : clear")
#@pg.production("update1 : drop")
#@pg.production("update1 : create")
#@pg.production("update1 : add")
#@pg.production("update1 : move")
#@pg.production("update1 : copy")
#@pg.production("update1 : insert_data")
#@pg.production("update1 : delete_data")
#@pg.production("update1 : delete_where")
#@pg.production("update1 : modify")
#def f(p): return p[0]
#pg.list("update1+", ";")

#@pg.production("load_part : INTO graph_ref")
#def f(p): return p
#pg.optional("load_part?")
#@pg.production("load : LOAD SILENT? iri load_part?")
#def f(p): return p

#@pg.production("clear : CLEAR SILENT? graph_ref_all")
#def f(p): return p

#@pg.production("drop : DROP SILENT? graph_ref_all")
#def f(p): return p

#@pg.production("create : CREATE SILENT? graph_ref")
#def f(p): return p

#@pg.production("add : ADD SILENT? graph_or_default TO graph_or_default")
#def f(p): return p

#@pg.production("move : MOVE SILENT? graph_or_default TO graph_or_default")
#def f(p): return p

#@pg.production("copy : COPY SILENT? graph_or_default TO graph_or_default")
#def f(p): return p

#@pg.production("insert_data : INSERT DATA quad_pattern")
#def f(p): return p

#@pg.production("delete_data : DELETE DATA quad_pattern")
#def f(p): return p

#@pg.production("delete_where : DELETE WHERE quad_pattern")
#def f(p): return p

@pg.production("with_iri : WITH IRI")
def f(p):
  translator = CURRENT_TRANSLATOR.get()
  p = p[1]
  p.value  = p.value[1:-1]
  if not ":" in p.value: p.value = "%s%s" % (translator.base_iri, p.value) # Relative IRI
  p.ontology = translator.world.get_ontology(p.value)
  return p
pg.optional("with_iri?")


def _scan_params(s, x):
  if   isinstance(x, (list, tuple)):
    for i in x: _scan_params(s, i)
  elif isinstance(x, rply.Token) and (x.name == "PARAM"):
    s.add(x.number)
    
def _rename_params(d, x):
  if   isinstance(x, (list, tuple)):
    for i in x: _rename_params(d, i)
  elif isinstance(x, rply.Token) and (x.name == "PARAM"):
    x.number = d[x.number]
    
def _create_modify_query(ontology_iri, deletes, inserts, using, group_graph_pattern, solution_modifier):
  translator = CURRENT_TRANSLATOR.get()
  selects = []
  vars    = set()
  for triple in inserts + deletes:
    for x in triple:
      if   (x.name == "VAR") and not x.value.startswith("??anon") and not x.value.startswith("_:") and not (x.value in vars):
        vars.add(x.value)
        selects.append(x)
        
  select_param_indexes = set()
  _scan_params(select_param_indexes, group_graph_pattern)
  select_param_indexes = sorted(select_param_indexes)
  old_2_new_param = { n : i+1 for i, n in enumerate(select_param_indexes) }
  _rename_params(old_2_new_param, group_graph_pattern)
  
  if isinstance(group_graph_pattern, NotExistsBlock): # FILTER NOT EXISTS alone; not supported as the main query.
    group_graph_pattern = SimpleTripleBlock([group_graph_pattern])
  main_query = translator.new_sql_query("main", group_graph_pattern, selects, None, solution_modifier)
  main_query.type                 = "modify"
  main_query.ontology_iri         = ontology_iri
  main_query.inserts              = inserts
  main_query.deletes              = deletes
  main_query.select_param_indexes = select_param_indexes
  return main_query

@pg.production("modify : with_iri? insert_clause using_clause*  WHERE group_graph_pattern solution_modifier")
def f(p): return _create_modify_query(p[0], [], p[1], p[2], p[4], p[5])
@pg.production("modify : with_iri? delete_clause using_clause*  WHERE group_graph_pattern solution_modifier")
def f(p): return _create_modify_query(p[0], p[1], [], p[2], p[4], p[5])
@pg.production("modify : with_iri? delete_clause insert_clause using_clause*  WHERE group_graph_pattern solution_modifier")
def f(p): return _create_modify_query(p[0], p[1], p[2], p[3], p[5], p[6])

#@pg.production("delete_clause : DELETE quad_pattern")
#@pg.production("insert_clause : INSERT quad_pattern")
@pg.production("delete_clause : DELETE { triples_same_subject_path+ }")
@pg.production("insert_clause : INSERT { triples_same_subject_path+ }")
def f(p):
  p = [j for i in p[2] for j in i]
  return p

@pg.production("using_clause : USING iri")
@pg.production("using_clause : USING NAMED iri")
def f(p): return p
pg.list("using_clause*", "")

#@pg.production("graph_or_default : GRAPH? iri")
#@pg.production("graph_or_default : DEFAULT")
#def f(p): return p
#pg.optional("GRAPH?")

#@pg.production("graph_ref : GRAPH iri")
#def f(p): return p

#@pg.production("graph_ref_all : graph_ref")
#@pg.production("graph_ref_all : DEFAULT")
#@pg.production("graph_ref_all : NAMED")
#@pg.production("graph_ref_all : ALL")
#def f(p): return p

#@pg.production("quad_pattern : { quads }")
#def f(p): return p[1]

#@pg.production("quads_part : quads_not_triples .? triples_template?")
#def f(p): return p
#pg.list("quads_part*", "")
#@pg.production("quads : triples_template? quads_part*")
#@pg.production("quads : triples_template?")
#def f(p): return p[0]

#@pg.production("quads_not_triples : GRAPH var_or_iri { triples_template? }")
#def f(p): return p

#@pg.production("triples_template : triples_same_subject+")
#def f(p): return p[0]
#pg.optional("triples_template?")

@pg.production("group_graph_pattern : { select_query }")
def f(p):
  r = SubQueryBlock(p[1])
  return r

@pg.production("group_graph_pattern : { group_graph_pattern_item* }")
def _create_simple_block(p, accept_static = True):
  r = SimpleTripleBlock()
  for i in p[1]:
    if   isinstance(i, Block) \
      or isinstance(i, Bind) \
      or isinstance(i, Filter):       r.append(i)
    elif isinstance(i, list):
      in_static = False
      for j in i:
        if in_static:
          static_triples.append(j)
          if j.end_sequence:
            _finalize_static(r, static_triples)
            in_static = False
        else:
          if accept_static and isinstance(j, Triple) and (j[1].modifier == "*STATIC"):
            j[1].modifier = "*"
            static_triples = [j]
            in_static = True
          else: r.append(j)
      if in_static: _finalize_static(r, static_triples)
          
    elif isinstance(i, StaticValues): r.static_valuess.append(i)
    else: raise ValueError
  if (len(r) == 1) and isinstance(r[0], Block) and (not r.static_valuess): return r[0]
  return r
pg.list("group_graph_pattern+", "UNION")

def _finalize_static(r, static_triples):
  s = _create_simple_block(["{", [static_triples], "}"], accept_static = False)
  static_block = StaticBlock(s)
  r.static_valuess.append(static_block)
  
#@pg.production("group_graph_pattern_item_triple_content : triples_same_subject_path+")
#def f(p): return p[0]
#@pg.production("group_graph_pattern_item_triple_content : FILTER constraint")
#def f(p): return Filter(p[1])
#@pg.production("group_graph_pattern_item_triple_content : BIND ( expression AS var )")
#def f(p): return Bind(p[2], p[4])
#pg.list("group_graph_pattern_item_triple_content+")
  
@pg.production("group_graph_pattern_item : triples_same_subject_path")
def f(p): return p[0]
@pg.production("group_graph_pattern_item : group_graph_pattern+") # UNION
def f(p):
  if len(p[0]) == 1: return p[0][0]
  return UnionBlock(p[0])
@pg.production("group_graph_pattern_item : OPTIONAL group_graph_pattern")
def f(p):
  p = list(p[1])
  if (len(p) == 1) and isinstance(p[0], Triple):
    p[0].optional = True
    return p
  return OptionalBlock(p)
@pg.production("group_graph_pattern_item : MINUS group_graph_pattern")
def f(p):
  return MinusBlock(p[1])
@pg.production("group_graph_pattern_item : FILTER constraint")
def f(p):
  if   isinstance(p[1], list) and isinstance(p[1][0], rply.Token) and p[1][0].name == "EXISTS":
    return ExistsBlock(p[1][1])
  elif isinstance(p[1], list) and isinstance(p[1][0], rply.Token) and p[1][0].name == "NOT_EXISTS":
    return NotExistsBlock(p[1][1])
  else:
    return Filter(p[1])
@pg.production("group_graph_pattern_item : BIND ( expression AS var )")
def f(p): return Bind(p[2], p[4])
#@pg.production("group_graph_pattern_item : GRAPH var_or_iri group_graph_pattern")
#@pg.production("group_graph_pattern_item : SERVICE SILENT? var_or_iri group_graph_pattern")

@pg.production("group_graph_pattern_item : inline_data")
def f(p): return p[0]

@pg.production("group_graph_pattern_item : STATIC group_graph_pattern")
def f(p): return StaticBlock(p[1])

pg.list("group_graph_pattern_item*", ".?")
pg.optional(".?")

@pg.production("inline_data : VALUES data_block")
def f(p): return p[1]

@pg.production("data_block : inline_data_one_var")
def f(p): return p[0]
@pg.production("data_block : inline_data_full")
def f(p): return p[0]

@pg.production("inline_data_one_var : var { data_block_value* }")
def f(p):
  static_values = StaticValues()
  static_values.vars.append(p[0])
  static_values.valuess.extend([i.sql] if hasattr(i, "sql") else [i.value]  for i in p[2])
  
  if p[2][0].name == "IRI": static_values.types.append("objs")
  else:                     static_values.types.append("datas")
  return static_values

#@pg.production("nil_or_var* : NIL")
#@pg.production("nil_or_var* : var*")
#def f(p): return p[0]
#@pg.production("data_block_value*_or_nil : NIL")
#@pg.production("data_block_value*_or_nil : ( data_block_value* )")
#def f(p): return p
#pg.list("data_block_value*_or_nil*", "")

@pg.production("data_block_values : ( data_block_value* )")
def f(p): return p[1]
pg.list("data_block_values*", "")

#@pg.production("inline_data_full : nil_or_var* { data_block_value*_or_nil* }")
@pg.production("inline_data_full : ( var* ) { data_block_values* }")
def f(p):
  static_values = StaticValues()
  for var in p[1]: static_values.vars.append(var)
  static_values.valuess.extend([i.sql if hasattr(i, "sql") else i.value for i in l] for l in p[4])
  
  for i in p[4][0]:
    if i.name == "IRI": static_values.types.append("objs")
    else:               static_values.types.append("datas")
  return static_values

@pg.production("data_block_value : iri")
@pg.production("data_block_value : rdf_literal")
@pg.production("data_block_value : numeric_literal")
@pg.production("data_block_value : undef")
def f(p): return p[0]
@pg.production("data_block_value : BOOL")
def f(p):
  p[0].value = "'%s'" % p[0].value
  return p[0]
pg.list("data_block_value*", "")


@pg.production("constraint : bracketted_expression")
@pg.production("constraint : builtin_call")
@pg.production("constraint : function_call")
def f(p): return p[0]
pg.list("constraint+", "")

@pg.production("function_call : iri arg_list")
def f(p): return p

@pg.production("arg_list : NIL")
@pg.production("arg_list : ( DISTINCT? expression+ )")
def f(p): return p

@pg.production("expression_list : NIL")
@pg.production("expression_list : ( expression+ )")
def f(p): return p

#@pg.production("construct_template : { construct_triples? }")
#def f(p): return p

#@pg.production("construct_triples_part : . construct_triples?")
#def f(p): return p
#pg.optional("construct_triples_part?")

#@pg.production("construct_triples : triples_same_subject construct_triples_part?")
#def f(p): return p
#pg.optional("construct_triples?")

#@pg.production("triples_same_subject : var_or_term property_list_not_empty")
#@pg.production("triples_same_subject : triples_node property_list_not_empty?")
#def f(p): return p
#pg.list("triples_same_subject+", ".")

@pg.production("property_list_not_empty_part : var_or_iri object+")
def f(p): return p
pg.list("property_list_not_empty_part+", ";")
@pg.production("property_list_not_empty : property_list_not_empty_part+ ")
def f(p): return p
#pg.optional("property_list_not_empty?")

def _expand_triple(triples, s, ps_os):
  for p, o in ps_os:
    #if p.modifier == "*STATIC":
    #  triples0 = triples
    #  triples  = []
    #  b = SimpleTripleBlock()
    #  static_group = StaticGroup(b)
    
    if   isinstance(p, rply.Token):
      if (p.name == "VAR") or (p.name == "PARAM"):
        p.inversed = False
        p.modifier = None
      _add_triple(triples, s, p, o)
      
    elif isinstance(p, NegatedPropPath):
      _add_triple(triples, s, p, o)
      
    elif isinstance(p, UnionPropPath):
      if p.modifier:
        _add_triple(triples, s, p, o)
      else:
        u = []
        for p1 in p:
          t = SimpleTripleBlock()
          if p.inversed: _expand_triple(t, o, [(p1, s)])
          else:          _expand_triple(t, s, [(p1, o)])
          u.append(t)
        triples.append(UnionBlock(u))
        
    elif isinstance(p, SequencePropPath):
      if p.modifier:
        raise NotImplementedError("Property path expressions of the form '(p1/p2)*' are not yet supported by Owlready2 native SPARQL engine. You may use RDFlib instead.")
      else:
        translator = CURRENT_TRANSLATOR.get()
        s2 = s
        for p2 in p:
          if p2 is p[-1]: o2 = o
          else:           o2 = rply.Token("VAR", translator.new_var())
          #_add_triple(triples, s2, p2, o2)
          _expand_triple(triples, s2, [(p2, o2)])
          s2 = o2
        triples[-1].end_sequence = True
        
    else: raise ValueError(p)
    
def _add_triple(triples, s, pr, o):
  if isinstance(s, list): s = _expand_blank(triples, s)
  if isinstance(o, list): o = _expand_blank(triples, o)
  if getattr(pr, "inversed", False): triples.append(Triple([o, pr, s]))
  else:                              triples.append(Triple([s, pr, o]))
  
def _expand_blank(triples, x):
  translator = CURRENT_TRANSLATOR.get()
  v = rply.Token("VAR", translator.new_var())
  assert x[0].name == "["
  x = x[1]
  _expand_triple(triples, v, x)
  return v
  
  
@pg.production("triples_same_subject_path : var_or_term property_list_path_not_empty")
@pg.production("triples_same_subject_path : triples_node_path property_list_path_not_empty?")
def f(p): # Expand ; in triples
  triples = []
  _expand_triple(triples, p[0], p[1])
  return triples
pg.list("triples_same_subject_path+", ".")

# @pg.production("property_list_path_not_empty_part : path graph_node+")
# @pg.production("property_list_path_not_empty_part : var graph_node+")
# def f(p): return p
# pg.list("property_list_path_not_empty_part*", ";")
# @pg.production("property_list_path_not_empty : path object_path+ ")
# @pg.production("property_list_path_not_empty : path object_path+ ; property_list_path_not_empty_part*")
# @pg.production("property_list_path_not_empty : var object_path+ ")
# @pg.production("property_list_path_not_empty : var object_path+ ; property_list_path_not_empty_part*")
# def f(p): return p
# pg.optional("property_list_path_not_empty?")

@pg.production("property_list_path_not_empty_part : path object_path+")
@pg.production("property_list_path_not_empty_part : var object_path+")
def f(p): return p
pg.list("property_list_path_not_empty_part+", ";")
@pg.production("property_list_path_not_empty : property_list_path_not_empty_part+")
def f(p): # Expand ',' in triples
  return [[pred, o] for pred, objs in p[0] for o in objs]
pg.optional("property_list_path_not_empty?")

@pg.production("path : path_sequence+")
def f(p):
  p = p[0]
  if len(p) == 1: return p[0]
  return UnionPropPath(p)

@pg.production("path_sequence : path_element_or_inverse+")
def f(p):
  p = p[0]
  if len(p) == 1: return p[0]
  return SequencePropPath(p)
pg.list("path_sequence+", "|")

@pg.production("path_element_or_inverse : path_element")
def f(p): return p[0]
@pg.production("path_element_or_inverse : ^ path_element")
def f(p):
  p = p[1]
  p.inversed = True
  return p
pg.list("path_element_or_inverse+", "/")

@pg.production("path_element : path_primary path_mod?")
def f(p):
  p[0].modifier = p[1] and p[1].value
  return p[0]

@pg.production("path_mod : ?")
@pg.production("path_mod : *STATIC")
@pg.production("path_mod : *")
@pg.production("path_mod : +")
def f(p): return p[0]
pg.optional("path_mod?")

@pg.production("path_primary : iri")
@pg.production("path_primary : param")
def f(p):
  p[0].inversed = False
  return p[0]
@pg.production("path_primary : ! path_negated_property_set")
def f(p):
  prop_path = NegatedPropPath()
  for i in p[1]: prop_path.append(i)
  return prop_path
@pg.production("path_primary : ( path )")
def f(p): return p[1]

@pg.production("path_negated_property_set : path_one_in_property_set")
def f(p): return p
@pg.production("path_negated_property_set : ( path_one_in_property_set+ )")
def f(p): return p[1]

@pg.production("path_one_in_property_set : iri")
def f(p):
  p[0].inversed = False
  return p[0]
@pg.production("path_one_in_property_set : ^ iri")
def f(p):
  p[0].inversed = True
  return p[0]
pg.list("path_one_in_property_set+", "|")


@pg.production("triples_node : collection")
@pg.production("triples_node : blank_node_property_list")
def f(p): return p[0]

@pg.production("blank_node_property_list : [ property_list_not_empty ]")
def f(p): return p

@pg.production("triples_node_path : collection_path")
def f(p): return p[0]
@pg.production("triples_node_path : [ property_list_path_not_empty ]")
def f(p): return p

@pg.production("collection : ( graph_node+ )")
def f(p): return p[1]
@pg.production("collection_path : ( graph_node_path+ )")
def f(p): return p[1]

@pg.production("object_path : graph_node_path")
def f(p): return p[0]
pg.list("object_path+", ",")

@pg.production("object : graph_node")
def f(p): return p[0]
pg.list("object+", ",")

@pg.production("graph_node : var")
@pg.production("graph_node : graph_term")
@pg.production("graph_node : triples_node")
def f(p): return p[0]
pg.list("graph_node+", "")

@pg.production("graph_node_path : var")
@pg.production("graph_node_path : graph_term")
@pg.production("graph_node_path : triples_node_path")
def f(p): return p[0]
pg.list("graph_node_path+", "")

@pg.production("var_or_term : var")
@pg.production("var_or_term : graph_term")
def f(p): return p[0]

@pg.production("var_or_iri : var")
@pg.production("var_or_iri : iri")
def f(p): return p[0]
pg.list("var_or_iri+", "")

@pg.production("var : VAR")
def f(p):
  p = p[0]
  if p.value.startswith("$"): p.value = "?%s" % p.value[1:]
  return p
pg.list("var*", "")

@pg.production("graph_term : iri")
@pg.production("graph_term : rdf_literal")
@pg.production("graph_term : numeric_literal")
@pg.production("graph_term : blank_node")
@pg.production("graph_term : NIL")
@pg.production("graph_term : param")
def f(p): return p[0]
@pg.production("graph_term : BOOL")
def f(p):
  p[0].value = "'%s'" % p[0].value
  return p[0]

@pg.production("param : PARAM")
def f(p):
  p = p[0]
  translator = CURRENT_TRANSLATOR.get()
  if len(p.value) > 2:
    p.number = int(p.value[2:])
    if p.number > translator.max_fixed_parameter: translator.max_fixed_parameter = p.number
  else:
    p.number = translator.new_parameter()
  return p

@pg.production("conditional_or_expression_operand : || conditional_and_expression")
def f(p):
  p[0].sql = "OR "
  return p
pg.list("conditional_or_expression_operand*", "")
@pg.production("expression : conditional_and_expression conditional_or_expression_operand*")
def f(p): return p
pg.list("expression*", ",", keep_sep = True)
pg.list("expression+", ",", keep_sep = True)

@pg.production("conditional_and_expression_operand : && relational_expression")
def f(p):
  p[0].sql = "AND "
  return p
pg.list("conditional_and_expression_operand*", "")
@pg.production("conditional_and_expression : relational_expression conditional_and_expression_operand*")
def f(p): return p

@pg.production("comparator : =")
@pg.production("comparator : COMPARATOR")
def f(p): return p[0]

@pg.production("relational_expression : numeric_expression")
@pg.production("relational_expression : numeric_expression comparator numeric_expression")
@pg.production("relational_expression : numeric_expression LIST_COMPARATOR expression_list")
def f(p): return p

#@pg.production("numeric_expression_operand : + multiplicative_expression multiplicative_expression_operand*")
#@pg.production("numeric_expression_operand : - multiplicative_expression multiplicative_expression_operand*")
#@pg.production("numeric_expression_operand : numeric_literal multiplicative_expression_operand*") # Probably an error in SPARQL grammar? This allows '2 * 2 2', but how is it suposed to be interpreted?
@pg.production("numeric_expression_operand : + multiplicative_expression")
@pg.production("numeric_expression_operand : - multiplicative_expression")
#def f(p): return p
def f(p): return [p[0], *p[1]]
pg.list("numeric_expression_operand*", "")
@pg.production("numeric_expression : multiplicative_expression numeric_expression_operand*")
#def f(p): return p
def f(p): return [p[0], *p[1]]

@pg.production("multiplicative_expression_operand : * unary_expression")
@pg.production("multiplicative_expression_operand : / unary_expression")
#def f(p): return p
def f(p): return [p[0], *p[1]]
pg.list("multiplicative_expression_operand*", "")
@pg.production("multiplicative_expression : unary_expression multiplicative_expression_operand*")
#def f(p): return p
def f(p):
  r = [*p[0]]
  for i in p[1]: r.extend(i)
  return r

@pg.production("unary_expression : ! primary_expression")
def f(p):
  p[0].sql = "NOT "
  return p
@pg.production("unary_expression : + primary_expression")
@pg.production("unary_expression : - primary_expression")
def f(p): return p
@pg.production("unary_expression : primary_expression")
def f(p): return p

@pg.production("primary_expression : bracketted_expression")
@pg.production("primary_expression : builtin_call")
@pg.production("primary_expression : iri_or_function")
@pg.production("primary_expression : rdf_literal")
@pg.production("primary_expression : numeric_literal")
@pg.production("primary_expression : var")
@pg.production("primary_expression : param")
def f(p): return p[0]
@pg.production("primary_expression : BOOL")
def f(p):
  p[0].value = "'%s'" % p[0].value
  return p[0]

@pg.production("bracketted_expression : ( expression )")
def f(p): return p

@pg.production("builtin_call : func")
@pg.production("builtin_call : aggregate")
@pg.production("builtin_call : exists")
@pg.production("builtin_call : not_exists")
def f(p): return p[0]

@pg.production("builtin_call : aggregate")
def f(p): return p[0]

@pg.production("func : iri ( expression* )")
def f(p):
  func_name = p[0].value.upper()
  p[0].name = "FUNC"
  return p
@pg.production("func : FUNC ( expression* )")
@pg.production("func : FUNC NIL")
def f(p):
  func_name = p[0].value.upper()
  if   func_name == "STRLEN":        p[0].sql = "LENGTH"
  elif func_name == "UCASE":         p[0].sql = "UPPER"
  elif func_name == "LCASE":         p[0].sql = "LOWER"
  elif func_name == "REPLACE":       p[0].sql = "SPARQL_REPLACE"
  elif func_name == "SIMPLEREPLACE": p[0].sql = "REPLACE"
  elif func_name == "IF":            p[0].sql = "IIF"
  elif func_name == "CONCAT":
    p[0].sql = ""
    for i in p[2]:
      if isinstance(i, rply.Token) and (i.name == ","): i.sql = "||"
      
  return p

pg.optional("DISTINCT?")

@pg.production("aggregate : AGGREGATE_FUNC ( DISTINCT? * )")
@pg.production("aggregate : AGGREGATE_FUNC ( DISTINCT? expression )")
@pg.production("aggregate : AGGREGATE_FUNC ( DISTINCT? expression ; SEPARATOR = string )")
def f(p):
  if p[2]: p[2].value += " "
  p[0].value = p[0].value.upper()
  p[0].name = "FUNC"
  if len(p) > 5:
    p[4:-1] = [rply.Token(",", ","), p[-2]]
  return p

@pg.production("exists : EXISTS group_graph_pattern")
def f(p): return p
@pg.production("not_exists : NOT_EXISTS group_graph_pattern")
def f(p): return p

pg.optional("arg_list?")

@pg.production("iri_or_function : iri arg_list?")
def f(p): return p

@pg.production("rdf_literal : string")
def f(p): return p[0]
@pg.production("rdf_literal : string LANG_TAG")
def f(p):
  p[0].value = locstr(p[0].value, p[1].value[1:])
  return p[0]
@pg.production("rdf_literal : string ^^ iri")
def f(p):
  translator = CURRENT_TRANSLATOR.get()
  p[0].name     = "DATA"
  p[0].datatype = translator.abbreviate(p[2].value)
  if   p[0].datatype in _INT_DATATYPES:   p[0].value = int  (p[0].value[1:-1])
  elif p[0].datatype in _FLOAT_DATATYPES: p[0].value = float(p[0].value[1:-1])
  #else:
  #  datatype_parser = _universal_abbrev_2_datatype_parser.get(p[0].datatype)
  #  if datatype_parser:
  #    p[0].value = datatype_parser[1](p[0].value[1:-1])
  return p[0]

_INT_DATATYPES   = { 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54 }
_FLOAT_DATATYPES = { 56, 57, 58, 59 }


@pg.production("numeric_literal : INTEGER")
def f(p):
  p = p[0]
  p.value = int(p.value)
  return p
@pg.production("numeric_literal : DECIMAL")
@pg.production("numeric_literal : DOUBLE")
def f(p):
  p = p[0]
  p.value = float(p.value)
  return p

@pg.production("string : STRING_LITERAL1")
def f(p):
  p = p[0]
  p.name  = "STRING"
  return p
@pg.production("string : STRING_LITERAL2")
def f(p):
  p = p[0]
  p.name  = "STRING"
  p.value = "'%s'" % p.value[1:-1].replace("'", r"\'")
  return p
@pg.production("string : STRING_LITERAL_LONG1")
@pg.production("string : STRING_LITERAL_LONG2")
def f(p):
  p = p[0]
  p.name = "STRING"
  p.value = "'%s'" % p.value[3:-3].replace("'", r"\'")
  return p

@pg.production("unabbreviated_iri : IRI")
def f(p):
  translator = CURRENT_TRANSLATOR.get()
  p = p[0]
  p.value  = p.value[1:-1]
  if not ":" in p.value: p.value = "%s%s" % (translator.base_iri, p.value) # Relative IRI
  return p
@pg.production("iri : IRI")
def f(p):
  translator = CURRENT_TRANSLATOR.get()
  p = p[0]
  p.value  = p.value[1:-1]
  if not ":" in p.value: p.value = "%s%s" % (translator.base_iri, p.value) # Relative IRI
  p.storid = p.sql = translator.abbreviate(p.value)
  return p
@pg.production("iri : PREFIXED_NAME")
def f(p):
  translator = CURRENT_TRANSLATOR.get()
  p = p[0]
  prefix, name = p.value.split(":", 1)
  p.name   = "IRI"
  p.value  = "%s%s" % (translator.expand_prefix("%s:" % prefix), name)
  p.storid = p.sql = translator.abbreviate(p.value)
  return p
@pg.production("iri : A")
def f(p):
  p = p[0]
  p.name   = "IRI"
  p.value  = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
  p.storid = p.sql = rdf_type
  return p

@pg.production("blank_node : BLANK_NODE_LABEL")
def f(p):
  p = p[0]
  p.name = "VAR"
  return p
@pg.production("blank_node : ANON")
def f(p):
  p = p[0]
  p.name   = "VAR"
  p.value  = CURRENT_TRANSLATOR.get().new_var()
  return p

@pg.production("undef : UNDEF")
def f(p):
  p = p[0]
  p.value = p.sql = "NULL"
  return p

PARSER = pg.build()
del lg, pg


CURRENT_TRANSLATOR = ContextVar("CURRENT_TRANSLATOR")

_DATA_TYPE  = { "STRING", "BOOL", "INTEGER", "DECIMAL", "DOUBLE", "DATA" }
_OBJ_PROPS  = { rdf_type, rdf_domain, rdf_range, rdfs_subclassof, rdfs_subpropertyof, owl_object_property, owl_inverse_property, owl_onproperty, owl_onclass, owl_ondatarange, owl_equivalentclass, owl_members, owl_distinctmembers, owl_unionof, owl_intersectionof, owl_oneof, SOME, ONLY, HAS_SELF }
_DATA_PROPS = { label.storid, comment.storid }


def _prefix_vars(x, prefix):
  for i in x:
    if   isinstance(i, Block): _prefix_vars(i, prefix)
    elif isinstance(i, rply.Token) and i.name == "VAR": i.value = "%s%s" % (prefix, i.value)
    
class Block(list):
  def __repr__(self):
    if getattr(self, "static_valuess", None): return "<%s %s static=%s>" % (self.__class__.__name__, list.__repr__(self), self.static_valuess)
    return "<%s %s>" % (self.__class__.__name__, list.__repr__(self))
  
  def get_ordered_vars(self):
    vars = set()
    ordered_vars = []
    self._get_ordered_vars(vars, ordered_vars, True)
    return ordered_vars
  
  def _get_ordered_vars(self, vars, ordered_vars, root_call = False): raise NotImplementedError
  
  def __hash__(self): return id(self)
  
class UnionBlock(Block):
  def __init__(self, l = None):
    Block.__init__(self, l or [])
    
    self.simple_union_triples = self._to_simple_union()
    
  def __repr__(self): return "<%s %s %s>" % (self.__class__.__name__, "Simple" if self.simple_union_triples else "Non-Simple", list.__repr__(self))
  
  def _to_simple_union(self):
    if len(self[0]) == 2:
      r = self._to_simple_union2()
      if r: return r
      
    for i in self:
      if not isinstance(i, SimpleTripleBlock): return None
      if len(i) > 1: return None
      if (not i): return None
      if (not isinstance(i[0], Triple)): return None
      
    ss = set()
    ps = set()
    os = set()
    mods = set()
    for i in self:
      ss.add(repr(i[0][0]))
      ps.add(repr(i[0][1]))
      os.add(repr(i[0][2]))
      mods.add(i[0][1].modifier)
    if len(mods) > 1: return None
    nb_many = 0
    if len(ss) > 1: nb_many += 1; n = 0
    if len(ps) > 1: nb_many += 1; n = 1
    if len(os) > 1: nb_many += 1; n = 2
    if nb_many > 1:  return None
    if nb_many == 0: return None
    if n == 1: # Prop; prop path modifier not supported in that case
      for i in self:
        if i[0][1].modifier: return None
        
    vs = [i[0][n] for i in self]
    for v in vs:
      if (not isinstance(v, rply.Token)) or (v.name != "IRI"): return None
      
    r = list(self[0][0])
    r[n] = SimpleUnion(vs)
    r = Triple(r)
    if n == 1:
      table_types = { i[0].table_type for i in self }
      if (len(table_types) > 1) or (table_types == { "quads" }): return None # quads is a virtual table; the "simple union" optimization does not benefit to such table in SQLite3
      r.table_type = tuple(table_types)[0]
    return [r]
  
  def _to_simple_union2(self):
    ss = set()
    for i in self:
      if len(i) != 2: return None
      if getattr(i[0][1], "storid", None) != rdf_type: return None
      if getattr(i[0][1], "modifier", None): return None
      if getattr(i[1][1], "storid", None) != rdfs_subclassof: return None
      if repr(i[0][2]) != repr(i[1][0]): return None
      ss.add(repr(i[0][0]))
    if len(ss) != 1: return None
    
    vs = [i[1][2] for i in self]
    return [self[0][0], Triple([self[0][1][0], self[0][1][1], SimpleUnion(vs)])]
  
      
  def _get_ordered_vars(self, vars, ordered_vars, root_call = False):
    union_vars = self[0].get_ordered_vars()
    for alternative in self[1:]:
      for v in set(union_vars) - set(alternative.get_ordered_vars()): union_vars.remove(v)
    for var in union_vars: _var_found(var, vars, ordered_vars)
    
    
class TripleBlock(Block): pass

def _var_found(var, vars, ordered_vars):
  if not var in vars:
    vars.add(var)
    ordered_vars.append(var)
    
class TripleBlockWithStatic(TripleBlock):
  def __init__(self, l = None):
    TripleBlock.__init__(self, l or [])

    if hasattr(l, "static_valuess"):
      self.static_valuess = l.static_valuess
    else:
      self.static_valuess = []
    
  def _get_ordered_vars(self, vars, ordered_vars, root_call = False):
    for triple in self:
      triple._get_ordered_vars(vars, ordered_vars)

    for static in self.static_valuess:
      static._get_ordered_vars(vars, ordered_vars)

          
class SimpleTripleBlock(TripleBlockWithStatic): pass
      
class OptionalBlock(TripleBlock):
  def _get_ordered_vars(self, vars, ordered_vars, root_call = False):
    for triple in self:
      triple._get_ordered_vars(vars, ordered_vars)
      
class FilterBlock(TripleBlockWithStatic):
  def _get_ordered_vars(self, vars, ordered_vars, root_call = False):
    if root_call: # Otherwise, defines no bindings
      for triple in self:
        triple._get_ordered_vars(vars, ordered_vars)
        
      for static in self.static_valuess:
        static._get_ordered_vars(vars, ordered_vars)
        
class ExistsBlock   (FilterBlock): pass
class NotExistsBlock(FilterBlock): pass
    
class MinusBlock(TripleBlock): pass

class SubQueryBlock(Block):
  def parse(self): return _parse_select_query(self)
  
  def _get_ordered_vars(self, vars, ordered_vars, root_call = False):
    for v in self[2]: _var_found(v.value, vars, ordered_vars)

      
class Triple(tuple):
  end_sequence = False
  def __init__(self, l):
    self.optional     = False
    self.likelihood_p = None
    self.likelihood_o = None
    self.var_names    = { x.value for x in self if x.name == "VAR" }
    p_storid = getattr(self[1], "storid", None)
    self.Prop = p_storid and CURRENT_TRANSLATOR.get().world._get_by_storid(p_storid)
    
    if   self[2].name == "IRI":          self.table_type = "objs"
    elif self[2].name in _DATA_TYPE:     self.table_type = "datas"
    elif p_storid in _OBJ_PROPS:         self.table_type = "objs"
    elif p_storid in _DATA_PROPS:        self.table_type = "datas"
    elif not self.Prop:                  self.table_type = "quads"
    elif isinstance(self.Prop, ObjectPropertyClass): self.table_type = "objs"
    elif isinstance(self.Prop, DataPropertyClass):   self.table_type = "datas"
    else:                                            self.table_type = "quads"
      
    
  def _get_ordered_vars(self, vars, ordered_vars):
    if self[1].inversed: triple = self[::-1]
    else:                triple = self
    for x in triple:
      if   x.name == "VAR": _var_found(x.value, vars, ordered_vars)
      elif isinstance(x, PropPath): x._get_ordered_vars(vars, ordered_vars)
      
  
class SpecialCondition(object): pass

class SimpleUnion(SpecialCondition):
  name     = "SIMPLE_UNION"
  modifier = None
  inversed = False
  def __init__(self, items):
    self.items = items

  def create_conditions(self, conditions, table, n):
    conditions.append("%s.%s IN (%s)" % (table.name, n, ",".join(str(p.storid) for p in self.items)))

  def __repr__(self): return "<SimpleUnion %s>" % self.items
  def __str__ (self): return ",".join(str(i) for i in self.items)
  
  
class PropPath(list):
  def __init__(self, l = None):
    list.__init__(self, l or [])
    self.inversed = False
    self.modifier = None
  __hash__ = object.__hash__
  
  def _get_ordered_vars(self, vars, ordered_vars):
    for x in self:
      if   x.name == "VAR": _var_found(x.value, vars, ordered_vars)
      elif isinstance(x, PropPath): x._get_ordered_vars(vars, ordered_vars)
      
class NegatedPropPath(PropPath, SpecialCondition):
  name = "NEGATED_PROP_PATH"
  def create_conditions(self, conditions, table, n):
    if len(self) == 1:
      conditions.append("%s.%s!=%s" % (table.name, n, self[0].storid))
    else:
      conditions.append("%s.%s NOT IN (%s)" % (table.name, n, ",".join(str(p.storid) for p in self)))
  def __repr__(self): return "!(%s)" % " ".join(repr(prop) for prop in self)
      
class SequencePropPath(PropPath):
  name = "SEQUENCE_PROP_PATH"
  def __repr__(self): return "(%s)" % "/".join(repr(prop) for prop in self)
  
class UnionPropPath(PropPath):
  name = "UNION_PROP_PATH"
  def __repr__(self): return "(%s)" % "|".join(repr(prop) for prop in self)
  

def _get_vars(x):
  for i in x:
    if   isinstance(i, rply.Token) and i.name == "VAR": yield i.value
    elif isinstance(i, (list, tuple)): yield from _get_vars(i)
  
class Bind(object):
  def __init__(self, expression, var):
    self.expression           = expression
    self.var                  = var
    self.referenced_var_names = set()
    self._extract_referenced_var_names(expression)
    self.var_names = self.referenced_var_names
    
  def _extract_referenced_var_names(self, expression):
    if isinstance(expression, list):
      for i in expression: self._extract_referenced_var_names(i)
    elif expression is None: pass
    elif expression.name == "VAR":
      self.referenced_var_names.add(expression.value)
      
  def _get_ordered_vars(self, vars, ordered_vars):
    _var_found(self.var.values, vars, ordered_vars)
  
  
class Filter(object):
  def __init__(self, constraint):
    self.constraint = constraint
    self.var_names = set(_get_vars(constraint))
    
  def _get_ordered_vars(self, vars, ordered_vars):
    for var in self.var_names:
      _var_found(var, vars, ordered_vars)
    
  
class StaticValues(object):
  def __init__(self):
    self.vars    = []
    self.valuess = []
    self.types   = []
    
  def _get_ordered_vars(self, vars, ordered_vars, root_call = False): pass
  
  def __repr__(self): return "VALUES (%s) %s" % (" ".join(repr(var) for var in self.vars), self.valuess)
  
  
class StaticBlock(StaticValues):
  def __init__(self, blocks):
    StaticValues.__init__(self)
    self.inner_blocks = blocks
    self.ordered_vars = list(_get_vars(blocks))
    self.all_vars     = set(_get_vars(blocks))
    
    self.old_translator = CURRENT_TRANSLATOR.get()
    self.translator = self.old_translator.make_translator()
    CURRENT_TRANSLATOR.set(self.translator)
    
    self.translator.main_query = self.translator.new_sql_query("main", self.inner_blocks, None, True)
    
    self.translator.main_query.type = "select"
    CURRENT_TRANSLATOR.set(self.old_translator)
    del self.old_translator
    
  def _get_ordered_vars(self, vars, ordered_vars, root_call = False):
    for var in self.ordered_vars: _var_found(var, vars, ordered_vars)
    
    
  def __repr__(self): return """<StaticBlock vars=%s>""" % ",".join(repr(var) for var in self.all_vars)
