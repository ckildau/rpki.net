# Configuring the RPKI CA tools: `rpki.conf`

This section describes `rpki.conf`, the the configuration file for the RPKI CA
tools.

The first subsection is a quick summary of the options you're most likely to
need to configure (or at least check) for a basic setup.

The rest of this section contains a more complete reference to the
configuration file and some of the things you might need to do with it if your
needs are more complex.

There are a lot of configuration options, but in most cases you will never
have to touch more than a few of them. Keep reading, and don't panic.

## Quick guide to the most common configuration options

This subsection describes only a handful of `rpki.conf` configuration options.
These are the ones you'll need to set, or at least check, as part of initial
installation. In general, the installation process will have already set sane
values for these, but you may need to a few of them depending on exactly what
you're doing.

The location of `rpki.conf` varies depending on the operating system you're
running and how you installed the software. Unless you did something unusual
during installation, it's either `/etc/rpki.conf` or
`/usr/local/etc/rpki.conf`.

  * All of the configuration options you're most likely to need to change are in the `[myrpki]` section of `rpki.conf`. 
    
    
    [myrpki]
    

  * You need to check the setting of `rpkid_server_host`. The installation process sets this to the fully-qualified DNS hostname of the server on which you installed the code, but if you use a service-specific DNS name for RPKI service you will need to change this option to match that service name. 
    
    
    rpkid_server_host               = rpkid.example.org
    

  * You need to set the value of `run_pubd` to reflect whether you intend to run your own RPKI publication server and rsync server. 
    
    
    run_pubd                        = yes
    

> or

    
    
    run_pubd                        = no
    

  * If you are running your own RPKI publication server, you need to check the setting of `pubd_server_host`. The installation process sets this to the fully-qualified DNS hostname of the server on which you installed the code, but if you use a service-specific DNS name for RPKI publication service you will need to change this option to match that service name. 
    
    
    pubd_server_host                = pubd.example.org
    

There are _many_ other configuration options, but setting the above correctly
should suffice to get you started with the default configuration. Read on for
details if you need to know more, otherwise go to [next steps][1].

## Configuration file syntax

The general format of `rpki.conf` is the same as the configuration language
used by many other programs, including the OpenSSL package. The file is
divided into "sections", labeled with square brackets; individual options
within a section look like variable assignments, with the option name on the
left and the option value on the right.

    
    
    [foo]
    
    bar = fred
    baz = 42
    

The configuration file parser supports a limited version of the macro facility
used in OpenSSL's configuration parser. An expression such as

    
    
    foo = ${bar::baz}
    

sets foo to the value of the baz variable from section bar.

The section name `ENV` is special: it refers to environment variables.

    
    
    home = ${ENV::HOME}
    

Each of the programs that make up the RPKI tookit can potentially take its own
configuration file, but for most uses this is unnecessarily complicated. The
recommended approach is to use a single configuration file, and to put all of
the parameters that a normal user might need to change into a single section
of that configuration file, then reference these common settings from the
program-specific sections of the configuration file via macro expansion.

The default name for the shared configuration file is `rpki.conf`. The
location of the system-wide `rpki.conf` file is selected by `./configure`
during installation. The default location is `/usr/local/etc/rpki.conf` when
building from source or on platforms like FreeBSD or MacOSX where packaged
software goes in the `/usr/local` tree; on GNU/Linux platforms, binary
packages will use `/etc/rpki.conf` per GNU/Linux convention.

Regardless of the default location, you can override the build-time default
filename at runtime if necessary by setting the `RPKI_CONF` environment
variable to the name of the configuration file you want to use. Most of the
programs also take a command-line option (generally "`-c`") specifying the
name of the configuration file; if both the command line option and the
environment variable are set, the command line option wins.

The installation process builds a sample configuration file `rpki.conf.sample`
and installs it alongside of `rpki.conf`. If you have no `rpki.conf`
installed, the installation process will copy `rpki.conf.sample` to
`rpki.conf`, but it will not overwrite an existing `rpki.conf` file.

## Too much information about `rpki.conf` options

The list of options that you can set in `rpki.conf` is ridiculously long. The
default configuration includes what we hope are reasonable default settings
for all of them, so in many cases you will never need to know about most of
these options. A number of the options for individual programs are specified
in terms of other options, using the macro facility [described above][2].

In general, if you don't understand what an option does, you probably should
leave it alone.

Detailed information about individual options is listed in separate sections,
one per section of `rpki.conf`. These documentation sections are generated
from the same source file as the sample configuration file.

  * [ Common Options ][3]
  * [ [myrpki] section ][4]
  * [ [rpkid] section ][5]
  * [ [irdbd] section ][6]
  * [ [pubd] section ][7]
  * [ [rootd] section ][8]
  * [ [web_portal] section ][9]
  * [ [autoconf] section ][10]

## rsyncd.conf

If you're running pubd, you'll also need to run rsyncd. Your rsyncd
configuration will need to match your pubd configuration in order for relying
parties to find the RPKI objects managed by pubd.

Here's a sample rsyncd.conf file:

    
    
    pid file        = /var/run/rsyncd.pid
    uid             = nobody
    gid             = nobody
    
    [rpki]
        use chroot          = no
        read only           = yes
        transfer logging    = yes
        path                = /some/where/publication
        comment             = RPKI publication
    

You may need to adapt this to your system. In particular, you will need to set
the `path` option to match the directory you named as
`publication_base_directory` in `rpki.conf`.

You may need to do something more complicated if you are already running
rsyncd for other purposes. See the `rsync(1)` and `rsyncd.conf(5)` manual
pages for more details.

## Running your own RPKI root

In general, we do not recommend running your own RPKI root environment, for
various reasons. If, however, you need to do so, you should read [ the
documentation for the [rootd] section ][8], and [ the instructions for
creating a RPKI root certificate ][11].

## Running rpkid or pubd on a different server

The default configuration runs rpkid, pubd (if enabled) and the back end code
all on the same server. For most purposes, this is fine, but in some cases you
might want to split these functions up among different servers. If you need to
do this, see [these instructions][12].

## Configuring the test harness

We expect the test harness to be of interest primarily to developers, but if
you need to understand how it works, you will probably want to read [these
instructions][13].

## Next steps

Once you've finished with configuration, the next thing you should read is the
[MySQL setup instructions][14].

   [1]: #_.wiki.doc.RPKI.CA.Configuration#nextsteps

   [2]: #_.wiki.doc.RPKI.CA.Configuration#syntax

   [3]: #_.wiki.doc.RPKI.CA.Configuration.Common

   [4]: #_.wiki.doc.RPKI.CA.Configuration.myrpki

   [5]: #_.wiki.doc.RPKI.CA.Configuration.rpkid

   [6]: #_.wiki.doc.RPKI.CA.Configuration.irdbd

   [7]: #_.wiki.doc.RPKI.CA.Configuration.pubd

   [8]: #_.wiki.doc.RPKI.CA.Configuration.rootd

   [9]: #_.wiki.doc.RPKI.CA.Configuration.web_portal

   [10]: #_.wiki.doc.RPKI.CA.Configuration.autoconf

   [11]: #_.wiki.doc.RPKI.CA.Configuration.CreatingRoot

   [12]: #_.wiki.doc.RPKI.CA.Configuration.DifferentServer

   [13]: #_.wiki.doc.RPKI.CA.Configuration.Tests

   [14]: #_.wiki.doc.RPKI.CA.MySQLSetup

