# Installation Using FreeBSD Ports

Port skeletons are available for FreeBSD from download.rpki.net. To use these,
you need to download the port skeletons then run them using your favorite
FreeBSD port installation tool.

## Manual Download

To download the port skeletons manually and install from them, do something
like this:

    
    
    for port in rpki-rp rpki-ca
    do
      fetch https://download.rpki.net/FreeBSD_Packages/${port}-port.tgz
      tar xf ${port}-port.tgz
      cd ${port}
      make install
      cd ..
      rm -rf ${port}
    done
    

After performing initial installation, you should customize the default
`rpki.conf` for your environment as necessary. In particular, you want to
change `handle` and `rpkid_server_host`. There are [obsessively detailed
instructions][1].

    
    
    emacs /usr/local/etc/rpki.conf
    

Again, you want to change `handle` and `rpkid_server_host` at the minimum.

To upgrade, you can perform almost the same steps, but the FreeBSD ports
system, which doesn't really know about upgrades, will require you to use the
`deinstall` and `reinstall` operations instead of plain `install`:

    
    
    for port in rpki-rp rpki-ca
    do
      fetch https://download.rpki.net/FreeBSD_Packages/${port}-port.tgz
      tar xf ${port}-port.tgz
      cd ${port}
      make deinstall
      make reinstall
      cd ..
      rm -rf ${port}
    done
    

After an upgrade, you may want to check the newly-installed
`/usr/local/etc/rpki.conf.sample` against your existing
`/usr/local/etc/rpki.conf` in case any important options have changed. We
generally try to keep options stable between versions, and provide sane
defaults where we can, but if you've done a lot of customization to your
`rpki.conf` you will want to keep track of this.

## Automated Download and Install with portmaster

There's a [script][2] you can use to automate the download steps above and
perform the updates using portmaster. First, download the script:

    
    
    fetch https://download.rpki.net/FreeBSD_Packages/rpki-portmaster.sh
    

Then, to install or upgrade, just execute the script:

    
    
    sh rpki-portmaster.sh
    

As with manual download (above) you should customize `rpki.conf` after initial
installation.

## Automated Download and Install with portupgrade

There's a [script][3] you can use to automate the download steps above and
perform the updates using portupgrade. First, download the script:

    
    
    fetch https://download.rpki.net/FreeBSD_Packages/rpki-portupgrade.sh
    

Next, you will need to add information about the RPKI ports to two variables
in `/usr/local/etc/pkgtools.conf` before portupgrade will know how to deal
with these ports:

    
    
    EXTRA_CATEGORIES = [
        'rpki',
    ]
    
    ALT_INDEX = [
        ENV['PORTSDIR'] + '/INDEX.rpki',
    ]
    

Once you have completed these steps, you can just execute the script to
install or upgrade the RPKI code:

    
    
    sh rpki-portupgrade.sh
    

As with manual download (above) you should customize `rpki.conf` after initial
installation.

   [1]: #_.wiki.doc.RPKI.CA.Configuration

   [2]: https://download.rpki.net/FreeBSD_Packages/rpki-portmaster.sh

   [3]: https://download.rpki.net/FreeBSD_Packages/rpki-portupgrade.sh

