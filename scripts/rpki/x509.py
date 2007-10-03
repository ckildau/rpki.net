# $Id$

"""One X.509 implementation to rule them all...

...and in the darkness hide the twisty maze of partially overlapping
X.509 support packages in Python.

There are several existing packages, none of which do quite what I
need, due to age, lack of documentation, specialization, or lack of
foresight on somebody's part (perhaps mine).  This module attempts to
bring together the functionality I need in a way that hides at least
some of the nasty details.  This involves a lot of format conversion.
"""

import POW, tlslite.api, POW.pkix, base64, time
import rpki.exceptions, rpki.resource_set, rpki.manifest

class PEM_converter(object):
  """Convert between DER and PEM encodings for various kinds of ASN.1 data."""

  def __init__(self, kind):    # "CERTIFICATE", "RSA PRIVATE KEY", ...
    self.b = "-----BEGIN %s-----" % kind
    self.e = "-----END %s-----"   % kind

  def looks_like_PEM(self, text):
    b = text.find(self.b)
    return b >= 0 and text.find(self.e) > b + len(self.b)

  def to_DER(self, pem):
    """Convert from PEM to DER."""
    lines = pem.splitlines(0)
    while lines and lines.pop(0) != self.b:
      pass
    while lines and lines.pop(-1) != self.e:
      pass
    assert lines
    return base64.b64decode("".join(lines))

  def to_PEM(self, der):
    """Convert from DER to PEM."""
    b64 =  base64.b64encode(der)
    pem = self.b + "\n"
    while len(b64) > 64:
      pem += b64[0:64] + "\n"
      b64 = b64[64:]
    return pem + b64 + "\n" + self.e + "\n"

class DER_object(object):
  """Virtual class to hold a generic DER object."""

  ## Formats supported in this object
  formats = ("DER",)

  ## PEM converter for this object
  pem_converter = None

  ## Other attributes that self.clear() should whack
  other_clear = ()

  ## @var DER
  ## DER value of this object

  def empty(self):
    """Test whether this object is empty."""
    for a in self.formats:
      if getattr(self, a, None) is not None:
        return False
    return True

  def clear(self):
    """Make this object empty."""
    for a in self.formats + self.other_clear:
      setattr(self, a, None)

  def __init__(self, **kw):
    self.clear()
    if len(kw):
      self.set(**kw)

  def set(self, **kw):
    """Set this object by setting one of its known formats.

    This method only allows one to set one format at a time.
    Subsequent calls will clear the object first.  The point of all
    this is to let the object's internal converters handle mustering
    the object into whatever format you need at the moment.
    """
    if len(kw) == 1:
      name = kw.keys()[0]
      if name in self.formats:
        self.clear()
        setattr(self, name, kw[name])
        return
      if name == "PEM":
        self.clear()
        self.DER = self.pem_converter.to_DER(kw[name])
        return
      if name == "Base64":
        self.clear()
        self.DER = base64.b64decode(kw[name])
        return
      if name in ("PEM_file", "DER_file", "Auto_file"):
        f = open(kw[name], "r")
        value = f.read()
        f.close()
        if name == "PEM_file" or (name == "Auto_file" and self.pem_converter.looks_like_PEM(value)):
          value = self.pem_converter.to_DER(value)
        self.clear()
        self.DER = value
        return
    raise rpki.exceptions.DERObjectConversionError, "Can't honor conversion request %s" % repr(kw)
  
  def get_DER(self):
    """Get the DER value of this object.

    Subclasses will almost certainly override this method.
    """
    assert not self.empty()
    if self.DER:
      return self.DER
    raise rpki.exceptions.DERObjectConversionError, "No conversion path to DER available"

  def get_Base64(self):
    """Get the Base64 encoding of the DER value of this object."""
    return base64.b64encode(self.get_DER())

  def get_PEM(self):
    """Get the PEM representation of this object."""
    return self.pem_converter.to_PEM(self.get_DER())

class X509(DER_object):
  """X.509 certificates.

  This class is designed to hold all the different representations of
  X.509 certs we're using and convert between them.  X.509 support in
  Python a nasty maze of half-cooked stuff (except perhaps for
  cryptlib, which is just different).  Users of this module should not
  have to care about this implementation nightmare.
  """

  formats = ("DER", "POW", "POWpkix", "tlslite")
  pem_converter = PEM_converter("CERTIFICATE")
  other_clear = ("POW_extensions",)
  
  def get_DER(self):
    """Get the DER value of this certificate."""
    assert not self.empty()
    if self.DER:
      return self.DER
    if self.POW:
      self.DER = self.POW.derWrite()
      return self.get_DER()
    if self.POWpkix:
      self.DER = self.POWpkix.toString()
      return self.get_DER()
    raise rpki.exceptions.DERObjectConversionError, "No conversion path to DER available"

  def get_POW(self):
    """Get the POW value of this certificate."""
    assert not self.empty()
    if not self.POW:
      self.POW = POW.derRead(POW.X509_CERTIFICATE, self.get_DER())
    return self.POW

  def get_POWpkix(self):
    """Get the POW.pkix value of this certificate."""
    assert not self.empty()
    if not self.POWpkix:
      cert = POW.pkix.Certificate()
      cert.fromString(self.get_DER())
      self.POWpkix = cert
    return self.POWpkix

  def get_tlslite(self):
    """Get the tlslite value of this certificate."""
    assert not self.empty()
    if not self.tlslite:
      cert = tlslite.api.X509()
      cert.parseBinary(self.get_DER())
      self.tlslite = cert
    return self.tlslite

  def getIssuer(self):
    """Get the issuer of this certificate."""
    return self.get_POW().getIssuer()

  def getSubject(self):
    """Get the subject of this certificate."""
    return self.get_POW().getSubject()

  def getNotBefore(self):
    """Get the inception time of this certificate."""
    return POW.pkix.utc2time(self.get_POW().getNotBefore())

  def getNotAfter(self):
    """Get the expiration time of this certificate."""
    return POW.pkix.utc2time(self.get_POW().getNotAfter())

  def _get_POW_extensions(self):
    """Parse extensions from the POW value of this certificate.

    Build a dictionary to ease lookup, and cache the result.
    """
    if not self.POW_extensions:
      cert = self.get_POW()
      exts = {}
      for i in range(cert.countExtensions()):
        x = cert.getExtension(i)
        exts[x[0]] = x[2]
      self.POW_extensions = exts
    return self.POW_extensions
    
  def get_AKI(self):
    """Get the AKI extension from this certificate."""
    return (self.get_POWpkix().getExtension((2, 5, 29, 35)) or ((), 0, None))[2]

  def get_SKI(self):
    """Get the SKI extension from this certificate."""
    return (self.get_POWpkix().getExtension((2, 5, 29, 14)) or ((), 0, None))[2]

  def gSKI(self):
    """Calculate g(SKI) for this certificate."""
    return base64.b64encode(self.get_SKI()).replace("+", "-").replace("/", "_")

  def get_3779resources(self, as_intersector = None, v4_intersector = None, v6_intersector = None):
    """Get RFC 3779 resources as rpki.resource_set objects."""
    as, v4, v6 = rpki.resource_set.parse_extensions(self.get_POWpkix().getExtensions())
    if as_intersector is not None:
      as = as.intersection(as_intersector)
    if v4_intersector is not None:
      v4 = v4.intersection(v4_intersector)
    if v6_intersector is not None:
      v6 = v6.intersection(v6_intersector)
    return as, v4, v6

  def issue(self, keypair, subject_key, serial, sia, aia, crldp, cn = None, notAfter = None, as = None, v4 = None, v6 = None, is_ca = True):

    now = time.time()

    aki = self.get_SKI()

    ski = POW.Digest(POW.SHA1_DIGEST)
    ski.update(subject_key)
    ski = ski.digest()

    if cn is None:
      cn = "".join(("%02X" % ord(i) for i in ski))

    if notAfter is None:
      notAfter = now + 30 * 24 * 60 * 60

    cert = POW.pkix.Certificate()
    cert.setVersion(2)
    cert.setSerial(serial)
    cert.setIssuer(self.get_POWpkix().getSubject())
    cert.setSubject(((((2, 5, 4, 3), ("printableString", cn)),),))
    cert.setNotBefore(("UTCTime", POW.pkix.time2utc(now)))
    cert.setNotAfter(("UTCTime", POW.pkix.time2utc(notAfter)))
    cert.tbs.subjectPublicKeyInfo.set(subject_key)

    exts = [ ("subjectKeyIdentifier",   False, ski),
             ("authorityKeyIdentifier", False, (aki, (), None)),
             ("cRLDistributionPoints",  False, ((("fullName", (("uri", crldp),)), None, ()),)),
             ("authorityInfoAccess",    False, aia),    # (((1, 3, 6, 1, 5, 5, 7, 48, 2), ('uri', 'rsync://repository.apnic.net/TRUSTANCHORS/apnic.cer')),)
             ("subjectInfoAccess",      False, sia),    # (((1, 3, 6, 1, 5, 5, 7, 48, 5), ('uri', 'rsync://repository.apnic.net/APNIC/q66IrWSGuBE7jqx8PAUHAlHCqRw/')),)
             ("certificatePolicies",    True,  (((1, 3, 6, 1, 5, 5, 7, 14, 2), ()),)) ]

    if is_ca:
      exts.append(("basicConstraints",  True,  (1, None)))
      exts.append(("keyUsage",          True,  (0, 0, 0, 0, 0, 1, 1)))
    else:
      exts.append(("keyUsage",          True,  (1,)))

    if as:
      exts.append(("sbgp-autonomousSysNum", True, (as.to_tuple(), None)))
    if v4 or v6:
      exts.append(("sbgp-ipAddrBlock", True, [x for x in (v4.to_tuple(), v6.to_tuple()) if x is not None]))

    for x in exts:
      x[0] = POW.pkix.obj2oid(x[0])
    cert.setExtensions(exts)

    cert.sign(keypair.get_POW(), POW.SHA256_DIGEST)

    return X509(POWpkix = cert)

class X509_chain(list):
  """Collections of certs.

  This class provides sorting and conversion functions for various
  packages.
  """

  def __init__(self, *args, **kw):
    if args:
      self[:] = args
    elif "PEM_files" in kw:
      self.load_from_PEM(kw["PEM_files"])
    elif "DER_files" in kw:
      self.load_from_DER(kw["DER_files"])
    elif "Auto_files" in kw:
      self.load_from_Auto(kw["Auto_files"])
    elif kw:
      raise TypeError

  def chainsort(self):
    """Sort a bag of certs into a chain, leaf first.

    Various other routines want their certs presented in this order.
    """
    bag = self[:]
    issuer_names = [x.getIssuer() for x in bag]
    subject_map = dict([(x.getSubject(), x) for x in bag])
    chain = []
    for subject in subject_map:
      if subject not in issuer_names:
        cert = subject_map[subject]
        chain.append(cert)
        bag.remove(cert)
    if len(chain) != 1:
      raise rpki.exceptions.NotACertificateChain, "Certificates in bag don't form a proper chain"
    while bag:
      cert = subject_map[chain[-1].getIssuer()]
      chain.append(cert)
      bag.remove(cert)
    self[:] = chain

  def tlslite_certChain(self):
    """Return a certChain in the format tlslite likes."""
    self.chainsort()
    return tlslite.api.X509CertChain([x.get_tlslite() for x in self])

  def tlslite_trustList(self):
    """Return a trustList in the format tlslite likes."""
    return [x.get_tlslite() for x in self]

  def clear(self):
    """Drop all certs from this bag onto the floor."""
    self[:] = []

  def load_from_PEM(self, files):
    """Load a set of certs from a list of PEM files."""
    self.extend([X509(PEM_file=f) for f in files])

  def load_from_DER(self, files):
    """Load a set of certs from a list of DER files."""
    self.extend([X509(DER_file=f) for f in files])

  def load_from_Auto(self, files):
    """Load a set of certs from a list of DER or PEM files (guessing)."""
    self.extend([X509(Auto_file=f) for f in files])

class PKCS10_Request(DER_object):
  """Class to hold a PKCS #10 request."""

  formats = ("DER", "POWpkix")
  pem_converter = PEM_converter("CERTIFICATE REQUEST")
  
  def get_DER(self):
    """Get the DER value of this certification request."""
    assert not self.empty()
    if self.DER:
      return self.DER
    if self.POWpkix:
      self.DER = self.POWpkix.toString()
      return self.get_DER()
    raise rpki.exceptions.DERObjectConversionError, "No conversion path to DER available"

  def get_POWpkix(self):
    """Get the POW.pkix value of this certification request."""
    assert not self.empty()
    if not self.POWpkix:
      req = POW.pkix.CertificationRequest()
      req.fromString(self.get_DER())
      self.POWpkix = req
    return self.POWpkix

  def check_valid_rpki(self):
    """Check this certification request to see whether it's a valid
    request for an RPKI certificate.  This is broken out of the
    up-down protocol code because it's somewhat involved and the
    up-down code doesn't need to know the details.

    Throws an exception if the request isn't valid, so if this method
    returns at all, the request is ok.
    """

    if not self.get_POWpkix().verify():
      raise rpki.exceptions.BadPKCS10, "Signature check failed"

    if self.get_POWpkix().certificationRequestInfo.version != 0:
      raise rpki.exceptions.BadPKCS10, "Bad version number %s" % self.get_POWpkix().certificationRequestInfo.version

    if oid2name.get(self.get_POWpkix().signatureAlgorithm) not in ("sha256WithRSAEncryption", "sha384WithRSAEncryption", "sha512WithRSAEncryption"):
      raise rpki.exceptions.BadPKCS10, "Bad signature algorithm %s" % self.get_POWpkix().signatureAlgorithm

    exts = self.getExtensions()
    for oid, critical, value in exts:
      if oid2name.get(oid) not in ("basicConstraints", "keyUsage", "subjectInfoAccess"):
        raise rpki.exceptions.BadExtension, "Forbidden extension %s" % oid
    req_exts = dict((oid2name[oid], value) for (oid, critical, value) in exts)

    if "basicConstraints" not in req_exts or not req_exts["basicConstraints"][0]:
      raise rpki.exceptions.BadPKCS10, "request for EE cert not allowed here"

    if req_exts["basicConstraints"][1] is not None:
      raise rpki.exceptions.BadPKCS10, "basicConstraints must not specify Path Length"

    if "keyUsage" in req_exts and (not req_exts["keyUsage"][5] or not req_exts["keyUsage"][6]):
      raise rpki.exceptions.BadPKCS10, "keyUsage doesn't match basicConstraints"

    for method, location in req_exts.get("subjectInfoAccess", ()):
      if oid2name.get(method) == "caRepository" and (location[0] != "uri" or (location[1].startswith("rsync://") and not location[1].endswith("/"))):
        raise rpki.exceptions.BadPKCS10, "Certificate request includes bad SIA component: %s" % location

    # This one is an implementation restriction.  I don't yet
    # understand what the spec is telling me to do in this case.
    assert "subjectInfoAccess" in req_exts, "Can't (yet) handle PKCS #10 without an SIA extension"

class RSA_Keypair(DER_object):
  """Class to hold an RSA key pair."""

  formats = ("DER", "POW", "tlslite")
  pem_converter = PEM_converter("RSA PRIVATE KEY")
  
  def get_DER(self):
    assert not self.empty()
    if self.DER:
      return self.DER
    if self.POW:
      self.DER = self.POW.derWrite(POW.RSA_PRIVATE_KEY)
      return self.get_DER()
    raise rpki.exceptions.DERObjectConversionError, "No conversion path to DER available"

  def get_POW(self):
    assert not self.empty()
    if not self.POW:
      self.POW = POW.derRead(POW.RSA_PRIVATE_KEY, self.get_DER())
    return self.POW

  def get_tlslite(self):
    assert not self.empty()
    if not self.tlslite:
      self.tlslite = tlslite.api.parsePEMKey(self.get_PEM(), private=True)
    return self.tlslite

  def generate(self, keylength):
    self.clear()
    self.set(POW=POW.Asymmetric(POW.RSA_CIPHER, keylength))

  def get_public_DER(self):
    return self.get_POW().derWrite(POW.RSA_PUBLIC_KEY)

class Manifest(DER_object):
  """Class to hold a signed manifest."""

  formats = ("DER", "POWpkix")
  pem_converter = PEM_converter("RPKI MANIFEST")
  
  def get_DER(self):
    """Get the DER value of this manifest."""
    assert not self.empty()
    if self.DER:
      return self.DER
    if self.POWpkix:
      self.DER = self.POWpkix.toString()
      return self.get_DER()
    raise rpki.exceptions.DERObjectConversionError, "No conversion path to DER available"

  def get_POWpkix(self):
    """Get the POW.pkix value of this manifest."""
    assert not self.empty()
    if not self.POWpkix:
      mani = rpki.manifest.Manifest()
      mani.fromString(self.get_DER())
      self.POWpkix = mani
    return self.POWpkix
