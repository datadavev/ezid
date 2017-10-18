# =============================================================================
#
# EZID :: binder_async.py
#
# Asynchronous N2T binder processing.
#
# Author:
#   Greg Janee <gjanee@ucop.edu>
#
# License:
#   Copyright (c) 2017, Regents of the University of California
#   http://creativecommons.org/licenses/BSD/
#
# -----------------------------------------------------------------------------

import django.conf
import uuid

import config
import ezidapp.models
import noid_egg
import register_async
import util

_daemonEnabled = [None]
_threadName = [None]

def _shadowArk (id):
  if id.startswith("ark:/"):
    return id[5:]
  elif id.startswith("doi:"):
    return util.doi2shadow(id[4:])
  elif id.startswith("uuid:"):
    return util.uuid2shadow(id[5:])
  else:
    assert False, "unhandled case"

def _overwrite (sh, row, id, metadata):
  m = register_async.callWrapper(sh, row, "noid_egg.getElements",
    noid_egg.getElements, _shadowArk(id))
  if m == None: m = {}
  for k, v in metadata.items():
    if m.get(k) == v:
      del m[k]
    else:
      m[k] = v
  for k in m.keys():
    if k not in metadata: m[k] = ""
  if len(m) > 0:
    register_async.callWrapper(sh, row, "noid_egg.setElements",
      noid_egg.setElements, _shadowArk(id), m)

def _delete (sh, row, id, metadata):
  register_async.callWrapper(sh, row, "noid_egg.deleteIdentifier",
    noid_egg.deleteIdentifier, _shadowArk(id))

def enqueueIdentifier (identifier, operation, blob):
  """
  Adds an identifier to the binder asynchronous processing queue.
  'identifier' should be the normalized, qualified identifier, e.g.,
  "doi:10.5060/FOO".  'operation' is the identifier operation and
  should be one of the strings "create", "modify", or "delete".
  'blob' is the identifier's metadata dictionary in blob form.
  """
  register_async.enqueueIdentifier(ezidapp.models.BinderQueue,
    identifier, operation, blob)

def getQueueLength ():
  """
  Returns the length of the binder queue.
  """
  return ezidapp.models.BinderQueue.objects.count()

def _loadConfig ():
  _daemonEnabled[0] = django.conf.settings.DAEMON_THREADS_ENABLED and\
    config.get("daemons.binder_enabled").lower() == "true"
  if _daemonEnabled[0]:
    _threadName[0] = uuid.uuid1().hex
    register_async.launch("binder", ezidapp.models.BinderQueue,
      _overwrite, _delete,
      int(config.get("daemons.binder_num_worker_threads")),
      int(config.get("daemons.binder_processing_idle_sleep")),
      int(config.get("daemons.binder_processing_error_sleep")),
      _daemonEnabled, _threadName)

_loadConfig()
config.registerReloadListener(_loadConfig)