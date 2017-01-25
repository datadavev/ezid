# =============================================================================
#
# EZID :: geometry_util.py
#
# Geometry-related utility functions.
#
# Author:
#   Greg Janee <gjanee@ucop.edu>
#
# License:
#   Copyright (c) 2017, Regents of the University of California
#   http://creativecommons.org/licenses/BSD/
#
# -----------------------------------------------------------------------------

import lxml.etree
import re

import util

# N.B.: the namespace for KML 2.3 is still 2.2.
_kmlNamespace = "http://www.opengis.net/kml/2.2"
_dataciteNamespace = "http://datacite.org/schema/kernel-4"

def _q (elementName):
  return "{%s}%s" % (_dataciteNamespace, elementName)

def _isDecimalFloat (s):
  return re.match("-?(\d+(\.\d*)?|\.\d+)$", s) != None

def kmlPolygonToDatacite (kml):
  """
  Converts a polygon defined in a KML
  <http://www.opengeospatial.org/standards/kml> version 2.2 or 2.3
  document to a DataCite 4.0 <geoLocationPolygon> element.  The return
  is a pair (lxml.etree.Element, [warning, ...]) if successful or a
  string error message if not.  The conversion fails for the usual
  reasons (malformed KML, etc.) but also if the document defines more
  than one geometry or does not define a polygon.  Polygon holes and
  non-zero altitude coordinates are ignored and result in warnings.
  """
  try:
    root = util.parseXmlString(kml)
  except Exception, e:
    return "XML parse error: " + util.formatException(e)
  if root.tag != "{%s}kml" % _kmlNamespace: return "not a KML document"
  ns = { "N": _kmlNamespace }
  n = root.xpath("//N:Polygon", namespaces=ns)
  if len(n) == 0: return "no polygon found"
  if len(n) > 1 or len(root.xpath("//N:Point", namespaces=ns)) > 0 or\
    len(root.xpath("//N:LineString", namespaces=ns)) > 0 or\
    len(root.xpath("//N:Model", namespaces=ns)) > 0 or\
    len(root.xpath("//N:Track", namespaces=ns)) > 0:
    return "document defines more than one geometry"
  innerBoundaryWarning =\
    (len(n[0].xpath("N:innerBoundaryIs", namespaces=ns)) > 0)
  n = n[0].xpath("N:outerBoundaryIs", namespaces=ns)
  if len(n) != 1: return "polygon contains zero or multiple outer boundaries"
  n = n[0].xpath("N:LinearRing", namespaces=ns)
  if len(n) != 1:
    return "polygon outer boundary contains zero or multiple linear rings"
  n = n[0].xpath("N:coordinates", namespaces=ns)
  if len(n) != 1:
    return "polygon outer boundary contains zero or multiple " +\
      "coordinates elements"
  output = lxml.etree.Element(_q("geoLocationPolygon"),
    nsmap={ None: _dataciteNamespace })
  altitudeWarning = False
  for ct in n[0].text.split():
    c = ct.split(",")
    if len(c) not in [2, 3] or not _isDecimalFloat(c[0]) or\
      not _isDecimalFloat(c[1]) or (len(c) == 3 and not _isDecimalFloat(c[2])):
      return "malformed coordinates"
    if float(c[0]) < -180 or float(c[0]) > 180 or\
      float(c[1]) < -90 or float(c[1]) > 90:
      return "coordinates out of range"
    p = lxml.etree.SubElement(output, _q("polygonPoint"))
    lxml.etree.SubElement(p, _q("pointLongitude")).text = c[0]
    lxml.etree.SubElement(p, _q("pointLatitude")).text = c[1]
    if len(c) == 3 and float(c[2]) != 0: altitudeWarning = True
  if len(output) < 4:
    return "polygon has insufficient coordinate tuples (4 required)"
  if float(output[0][0].text) != float(output[-1][0].text) or\
    float(output[0][1].text) != float(output[-1][1].text):
    return "polygon first coordinate does not match last"
  warnings = []
  if innerBoundaryWarning: warnings.append("polygon inner boundaries ignored")
  if altitudeWarning: warnings.append("altitude coordinates ignored")
  return (output, warnings)
