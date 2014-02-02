from django import template
from django.conf import settings
from django.utils.html import escape
from decorators import basictag
from django.core.urlresolvers import reverse
from operator import itemgetter
import django.template
import urllib
import re
#import pdb
#import datetime

register = template.Library()

# settings value
@register.simple_tag
def settings_value(name):
  """ Gets a value from the settings configuration"""
  try:
    return settings.__getattr__(name)
  except AttributeError:
    return ""
  
@register.simple_tag
def choices(name, value, choice_string):
  """Creates radio buttons (for simple admin email form) based on string choices separated by a pipe"""
  choices = choice_string.split("|")
  return "  ".join(
          ['<input type="radio" name="' + name + '" value="' + escape(x) + '"' +
            (' checked="checked"' if value == x else '') + '>' + escape(x) + '</input>'
           for x in choices])

@register.tag
@basictag(takes_context=True) 
def request_value(context, key_name):
  """Outputs the value of context[key_name], required because
  normal django templating will not retrieve any variables starting with an underscore
  which all of the internal profile variables have"""
  request = context['request']
  if key_name in request.REQUEST:
    return escape(request.REQUEST[key_name])
  else:
    return ''
  
@register.tag
@basictag(takes_context=True) 
def set_dict_value(context, dt, key_name):
  """Sets value in the context object equal to the dictionary dt[key_name]"""
  context['value'] = dt[key_name]
  return ''

@register.simple_tag
def get_dict_value(dt, key_name):
  """For getting dictionary values which Django templating can't handle,
  such as those starting with underscore or with a dot in them"""
  if key_name in dt:
    return escape(dt[key_name])
  else:
    return ''
  
@register.simple_tag
def tooltip_class(profile_element_string):
  return escape('element_' + profile_element_string.replace('.',''))

@register.simple_tag
def identifier_display(id_text, testPrefixes):
  for pre in testPrefixes:
    if id_text.startswith(pre['prefix']):
      return "<span class='fakeid'>" + escape(id_text) + "</span>"
  return escape(id_text)

@register.simple_tag
def active_id_display(id_text, testPrefixes):
  #remove yellow highlighting for demo_id's URL
  #for pre in testPrefixes:
  #  if id_text.startswith(pre['prefix']):
  #    return "<span class='fakeid'>" + '<a href="' + _urlForm(id_text) + '">' + _urlForm(id_text) + '</a></span>'
  return '<a href="' + _urlForm(id_text) + '">' + _urlForm(id_text) + '</a>'
  
@register.simple_tag
def help_icon(id_of_help):
  return '&nbsp;&nbsp;&nbsp;&nbsp;<a href="#' + id_of_help + '" name="help_link">' + \
    '<img src="/static/images/help_icon.gif" alt="Click for additional help"' + \
    ' title="Click for additional help"/></a>'
    
@register.simple_tag
def datacite_field_help_icon(id_of_help):
  temp_id = id_of_help.replace(".", "_") + '_help'
  return '<div class="datacite_help">' + \
    '<a href="#' + temp_id + '" name="help_link">' + \
    '<img src="/static/images/help_icon.gif" alt="Click for additional help" title="Click for additional help"/>' + \
    '</a></div>'


@register.tag
@basictag(takes_context=True)
def host_based_include(context, template_path):
  """This includes a file from a different directory instead of the
  normal specified file based on the hostname.  This allows for some
  simple branding changes in the templates based host name differences"""
  request = context['request']
  host = request.META.get("HTTP_HOST", "default")
  if host not in django.conf.settings.LOCALIZATIONS: host = "default"
  template_path = template_path.replace("/_/",
    "/%s/" % django.conf.settings.LOCALIZATIONS[host][0])
  t = django.template.loader.get_template(template_path)
  return t.render(context)

#@register.simple_tag(takes_context=True)
@register.tag
@basictag(takes_context=True) 
def form_or_dict_value(context, dict, key_name):
  """Outputs the value of the dict[key_name] unless request.POST contains the data
  for the item which then overrides the dictionary's value.
  This both fixes problems with normal django templating which will not retrieve
  any keys starting with an underscore and it solves the problem of re-POSTed values
  which were getting clobbered by the stored values.  POSTed values should override
  so people do not lose their in-process edits.
  """
  request = context['request']
  if request.POST and key_name in request.POST:
    return escape(request.POST[key_name])
    #return escape(request['POST'][key_name])
  elif key_name in dict:
    return escape(dict[key_name])
  else:
    return ''
  
@register.tag
@basictag(takes_context=True) 
def form_or_default(context, key_name, default):
  """Outputs the value of the reposted value unless it doesn't exist then 
  outputs the default value passed in.
  """
  request = context['request']
  if key_name in request.REQUEST and request.REQUEST[key_name] != '':
    return escape(request.REQUEST[key_name])
  else:
    return escape(default)

@register.tag
@basictag(takes_context=True)
def selected_radio(context, request_item, loop_index, item_value):
  """returns checked="checked" if this should be the currently selected
  radio button based on matching request data or 1st item and nothing selected"""
  request = context['request']
  if request_item in request.REQUEST and request.REQUEST[request_item] == item_value:
    return 'checked="checked"'
  elif request_item not in request.REQUEST and loop_index == 1:
    return 'checked="checked"'
  else:
    return ''

@register.simple_tag
def shoulder_display(prefix_dict, testPrefixes, simple_display):
  display_prefix = ""
  for pre in testPrefixes:
    if prefix_dict['prefix'].startswith(pre['prefix']):
      display_prefix = " (<span class='fakeid'>" + escape(prefix_dict['prefix']) + "</span>)"
  if display_prefix == '':
    display_prefix = " (" + prefix_dict['prefix'] + ")"
  if simple_display == "True":
    t = re.search('^[A-Za-z]+:', prefix_dict['prefix'])
    t = t.group(0)[:-1].upper()
    return escape(t) + display_prefix
  else:
    type = prefix_dict['prefix'].split(":")[0].upper()
    return escape(prefix_dict['namespace'] + ' ' + type) + display_prefix 

@register.simple_tag
def search_display(dictionary, field):
  if field in ['createTime', 'updateTime']:
    return escape(datetime.datetime.fromtimestamp(dictionary[field]))
  else:
    return dictionary[field]
  
@register.simple_tag
def unavailable_codes(for_field):
  items = ( ("unac", "temporarily inaccessible"),
            ("unal", "unallowed, suppressed intentionally"),
            ("unap", "not applicable, makes no sense"),
            ("unas", "value unassigned (e.g., Untitled)"),
            ("unav", "value unavailable, possibly unknown"),
            ("unkn", "known to be unknown (e.g., Anonymous, Inconnue)"),
            ("none", "never had a value, never will"),
            ("null", "explicitly and meaningfully empty"),
            ("tba", "to be assigned or announced later"),
            ("etal", "too numerous to list (et alia)"),
            ("at", "the real value is at the given URL or identifier") )
  return "<ul>" + "\n".join(
          ["<li><a href=\"#"+ escape(x[0]) + "_" + for_field + "\" name=\"code_insert_link\">" + \
           escape("(:" + x[0] + ")" ) + "</a> " + escape(x[1]) + "</li>" for \
           x in items]
          ) + "</ul>"
    #<li><a href="#unas_datacite.creator" name="code_insert_link">(:unac)</a> temporarily inacessible</li>

# This function should and will be moved to a better location.  -GJ
def _urlForm (id):
  if id.startswith("doi:"):
    return "http://dx.doi.org/" + urllib.quote(id[4:], ":/")
  elif id.startswith("ark:/") or id.startswith("urn:uuid:"):
    return "http://n2t.net/" + urllib.quote(id, ":/")
  else:
    return "[None]"

@register.tag
@basictag(takes_context=True)
def full_url_to_id_details(context, id_text):
  """return URL form of identifier"""
  return _urlForm(id_text)
  
@register.tag
@basictag(takes_context=True)
def full_url_to_id_details_urlencoded(context, id_text):
  """return URL form of identifier, URL-encoded"""
  return urllib.quote(_urlForm(id_text))

#check for more than one of the same identifer type
#NOT checking for duplicate shoulders, returns t/f
@register.filter(name='duplicate_id_types')
def duplicate_id_types(prefixes):
  kinds = {}
  for prefix in prefixes:
    t = re.search('^[A-Za-z]+:', prefix['prefix'])
    t = t.group(0)[:-1]
    if t in kinds:
      kinds[t] = kinds[t] + 1
    else:
      kinds[t] = 1
  for key, value in kinds.iteritems():
    if value > 1:
      return True
  return False

#returns list of unique ID types such as ARK/DOI/URN with the
#prefix information, ((prefix, prefix_obj), etc)
#should only be called where only one prefix per type
@register.filter(name='unique_id_types')
def unique_id_types(prefixes):
  kinds = {}
  for prefix in prefixes:
    t = re.search('^[A-Za-z]+:', prefix['prefix'])
    t = t.group(0)[:-1]
    kinds[t] = prefix
  i = [(x[0].upper(), x[1],) for x in kinds.items()]
  return sorted(i, key = itemgetter(0))
  
#This captures the block around which rounded corners go
@register.tag(name="rounded_borders")
def do_rounded_borders(parser, token):
  nodelist = parser.parse(('endrounded_borders'))
  parser.delete_first_token()
  return FormatRoundedBordersNode(nodelist)

class FormatRoundedBordersNode(template.Node):
  def __init__(self,nodelist):
    self.nodelist = nodelist

  def render(self, context):
    content = self.nodelist.render(context)
    return """<div class="roundbox">
        <img src="/static/images/corners/tl.gif" width="6" height="6" class="roundtl" />
        <img src="/static/images/corners/tr.gif" width="6" height="6" class="roundtr" />
        <img src="/static/images/corners/bl.gif" width="6" height="6" class="roundbl" />
        <img src="/static/images/corners/br.gif" width="6" height="6" class="roundbr" />
        <div class="roundboxpad">
    %(content)s
    </div></div>""" % {'content':content,}
    

  
