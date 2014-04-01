# $Id$
#
# Copyright (C) 2014  Dragon Research Labs ("DRL")
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND DRL DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS.  IN NO EVENT SHALL DRL BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE
# OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

"""
Schedule action to force certificate reissuance as part of upgrade to
version 0.5678 of the rpki-ca toolkit.

This code is evaluated in the context of rpki-sql-setup's
do_apply_upgrades() function and has access to its variables.
"""

# Real work here has to be a deferred upgrade because the daemons have
# to be running for anything useful to happen.

db.add_deferred_upgrade('''

print """
        Version 0.5678 included a change which changed publication
        URIs embedded in issued certificates, which requires reissuing
        all affected certificates before everything will really work
        properly again.  Attempting to do this automatically...
"""

import subprocess, time

print "Pausing to let RPKI daemons start up"
time.sleep(10)

def rpkic(cmd):
  subprocess.check_call(("rpkic", "-i", handle, cmd))

handles = subprocess.check_output(("rpkic", "list_self_handles")).splitlines()

for handle in handles:

  print "Processing", handle

  print "Asking parent to reissue with new key"
  rpkic("up_down_rekey")

  print "Asking parent to revoke old key"
  rpkic("up_down_revoke")

  print "Reissuing everything"
  rpkic("force_reissue")

  print "Forcing publication"
  rpkic("force_publication")

del rpkic

''')
