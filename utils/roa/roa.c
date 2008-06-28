/*
 * Copyright (C) 2008  American Registry for Internet Numbers ("ARIN")
 *
 * Permission to use, copy, modify, and distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND ARIN DISCLAIMS ALL WARRANTIES WITH
 * REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
 * AND FITNESS.  IN NO EVENT SHALL ARIN BE LIABLE FOR ANY SPECIAL, DIRECT,
 * INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
 * LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE
 * OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
 * PERFORMANCE OF THIS SOFTWARE.
 */

/* $Id$ */

/*
 * Decoder test for ROAs.
 *
 * NB: This does -not- check the CMS signatures, just the encoding.
 */

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <unistd.h>
#include <string.h>

#include <openssl/bio.h>
#include <openssl/pem.h>
#include <openssl/err.h>
#include <openssl/x509.h>
#include <openssl/x509v3.h>
#include <openssl/safestack.h>
#include <openssl/conf.h>
#include <openssl/rand.h>
#include <openssl/asn1.h>
#include <openssl/asn1t.h>
#include <openssl/cms.h>

/*
 * How much buffer space do we need for a raw address?
 */
#define ADDR_RAW_BUF_LEN	16



/*
 * ASN.1 templates.  Not sure that ASN1_EXP_OPT() is the right macro
 * for these defaulted "version" fields, but it's what the examples
 * for this construction use.  Probably doesn't matter since this
 * program only decodes manifests, never encodes them.
 */

typedef struct ROAIPAddress_st {
  ASN1_BIT_STRING *IPAddress;
  ASN1_INTEGER *maxLength;
} ROAIPAddress;

DECLARE_STACK_OF(ROAIPAddress)

ASN1_SEQUENCE(ROAIPAddress) = {
  ASN1_SIMPLE(ROAIPAddress, IPAddress, ASN1_BIT_STRING),
  ASN1_EXP_OPT(ROAIPAddress, maxLength, ASN1_INTEGER, 0)
} ASN1_SEQUENCE_END(ROAIPAddress)

typedef struct ROAIPAddressFamily_st {
  ASN1_OCTET_STRING *addressFamily;
  STACK_OF(ROAIPAddress) *addresses;
} ROAIPAddressFamily;

DECLARE_STACK_OF(ROAIPAddressFamily)

ASN1_SEQUENCE(ROAIPAddressFamily) = {
  ASN1_SIMPLE(ROAIPAddressFamily, addressFamily, ASN1_OCTET_STRING),
  ASN1_SEQUENCE_OF(ROAIPAddressFamily, addresses, ROAIPAddress)
} ASN1_SEQUENCE_END(ROAIPAddressFamily)

typedef struct ROA_st {
  ASN1_INTEGER *version, *asID;
  STACK_OF(ROAIPAddressFamily) *ipAddrBlocks;
} ROA;

ASN1_SEQUENCE(ROA) = {
  ASN1_EXP_OPT(ROA, version, ASN1_INTEGER, 0),
  ASN1_SIMPLE(ROA, asID, ASN1_INTEGER),
  ASN1_SEQUENCE_OF(ROA, ipAddrBlocks, ROAIPAddressFamily)
} ASN1_SEQUENCE_END(ROA)

DECLARE_ASN1_FUNCTIONS(ROAIPAddress)
DECLARE_ASN1_FUNCTIONS(ROAIPAddressFamily)
DECLARE_ASN1_FUNCTIONS(ROA)

IMPLEMENT_ASN1_FUNCTIONS(ROAIPAddress)
IMPLEMENT_ASN1_FUNCTIONS(ROAIPAddressFamily)
IMPLEMENT_ASN1_FUNCTIONS(ROA)

#define sk_ROAIPAddress_new(st)				SKM_sk_new(ROAIPAddress, (st))
#define sk_ROAIPAddress_new_null()			SKM_sk_new_null(ROAIPAddress)
#define sk_ROAIPAddress_free(st)			SKM_sk_free(ROAIPAddress, (st))
#define sk_ROAIPAddress_num(st)				SKM_sk_num(ROAIPAddress, (st))
#define sk_ROAIPAddress_value(st, i)			SKM_sk_value(ROAIPAddress, (st), (i))
#define sk_ROAIPAddress_set(st, i, val)			SKM_sk_set(ROAIPAddress, (st), (i), (val))
#define sk_ROAIPAddress_zero(st)			SKM_sk_zero(ROAIPAddress, (st))
#define sk_ROAIPAddress_push(st, val)			SKM_sk_push(ROAIPAddress, (st), (val))
#define sk_ROAIPAddress_unshift(st, val)		SKM_sk_unshift(ROAIPAddress, (st), (val))
#define sk_ROAIPAddress_find(st, val)			SKM_sk_find(ROAIPAddress, (st), (val))
#define sk_ROAIPAddress_find_ex(st, val)		SKM_sk_find_ex(ROAIPAddress, (st), (val))
#define sk_ROAIPAddress_delete(st, i)			SKM_sk_delete(ROAIPAddress, (st), (i))
#define sk_ROAIPAddress_delete_ptr(st, ptr)		SKM_sk_delete_ptr(ROAIPAddress, (st), (ptr))
#define sk_ROAIPAddress_insert(st, val, i)		SKM_sk_insert(ROAIPAddress, (st), (val), (i))
#define sk_ROAIPAddress_set_cmp_func(st, cmp)		SKM_sk_set_cmp_func(ROAIPAddress, (st), (cmp))
#define sk_ROAIPAddress_dup(st)				SKM_sk_dup(ROAIPAddress, st)
#define sk_ROAIPAddress_pop_free(st, free_func)		SKM_sk_pop_free(ROAIPAddress, (st), (free_func))
#define sk_ROAIPAddress_shift(st)			SKM_sk_shift(ROAIPAddress, (st))
#define sk_ROAIPAddress_pop(st)				SKM_sk_pop(ROAIPAddress, (st))
#define sk_ROAIPAddress_sort(st)			SKM_sk_sort(ROAIPAddress, (st))
#define sk_ROAIPAddress_is_sorted(st)			SKM_sk_is_sorted(ROAIPAddress, (st))

#define sk_ROAIPAddressFamily_new(st)			SKM_sk_new(ROAIPAddressFamily, (st))
#define sk_ROAIPAddressFamily_new_null()		SKM_sk_new_null(ROAIPAddressFamily)
#define sk_ROAIPAddressFamily_free(st)			SKM_sk_free(ROAIPAddressFamily, (st))
#define sk_ROAIPAddressFamily_num(st)			SKM_sk_num(ROAIPAddressFamily, (st))
#define sk_ROAIPAddressFamily_value(st, i)		SKM_sk_value(ROAIPAddressFamily, (st), (i))
#define sk_ROAIPAddressFamily_set(st, i, val)		SKM_sk_set(ROAIPAddressFamily, (st), (i), (val))
#define sk_ROAIPAddressFamily_zero(st)			SKM_sk_zero(ROAIPAddressFamily, (st))
#define sk_ROAIPAddressFamily_push(st, val)		SKM_sk_push(ROAIPAddressFamily, (st), (val))
#define sk_ROAIPAddressFamily_unshift(st, val)		SKM_sk_unshift(ROAIPAddressFamily, (st), (val))
#define sk_ROAIPAddressFamily_find(st, val)		SKM_sk_find(ROAIPAddressFamily, (st), (val))
#define sk_ROAIPAddressFamily_find_ex(st, val)		SKM_sk_find_ex(ROAIPAddressFamily, (st), (val))
#define sk_ROAIPAddressFamily_delete(st, i)		SKM_sk_delete(ROAIPAddressFamily, (st), (i))
#define sk_ROAIPAddressFamily_delete_ptr(st, ptr)	SKM_sk_delete_ptr(ROAIPAddressFamily, (st), (ptr))
#define sk_ROAIPAddressFamily_insert(st, val, i)	SKM_sk_insert(ROAIPAddressFamily, (st), (val), (i))
#define sk_ROAIPAddressFamily_set_cmp_func(st, cmp)	SKM_sk_set_cmp_func(ROAIPAddressFamily, (st), (cmp))
#define sk_ROAIPAddressFamily_dup(st)			SKM_sk_dup(ROAIPAddressFamily, st)
#define sk_ROAIPAddressFamily_pop_free(st, free_func)	SKM_sk_pop_free(ROAIPAddressFamily, (st), (free_func))
#define sk_ROAIPAddressFamily_shift(st)			SKM_sk_shift(ROAIPAddressFamily, (st))
#define sk_ROAIPAddressFamily_pop(st)			SKM_sk_pop(ROAIPAddressFamily, (st))
#define sk_ROAIPAddressFamily_sort(st)			SKM_sk_sort(ROAIPAddressFamily, (st))
#define sk_ROAIPAddressFamily_is_sorted(st)		SKM_sk_is_sorted(ROAIPAddressFamily, (st))



/*
 * Expand the bitstring form of an address into a raw byte array.
 * At the moment this is coded for simplicity, not speed.
 */
static void addr_expand(unsigned char *addr,
			const ASN1_BIT_STRING *bs,
			const int length)
{
  assert(bs->length >= 0 && bs->length <= length);
  if (bs->length > 0) {
    memcpy(addr, bs->data, bs->length);
    if ((bs->flags & 7) != 0) {
      unsigned char mask = 0xFF >> (8 - (bs->flags & 7));
      addr[bs->length - 1] &= ~mask;
    }
  }
  memset(addr + bs->length, 0, length - bs->length);
}

/*
 * Extract the prefix length from a bitstring.
 */
#define addr_prefixlen(bs) ((int) ((bs)->length * 8 - ((bs)->flags & 7)))

/*
 * Read ROA (CMS object) in DER format.
 *
 * NB: When invoked this way, CMS_verify() does -not- verify, it just decodes the ASN.1.
 */
static const ROA *read_roa(const char *filename, const int print_cms, const int print_roa, const int print_signerinfo)
{
  unsigned char addr[ADDR_RAW_BUF_LEN];
  CMS_ContentInfo *cms = NULL;
  const ASN1_OBJECT *oid = NULL;
  const ROA *r = NULL;
  char buf[512];
  BIO *b;
  int i, j, k, n;

  if ((b = BIO_new_file(filename, "r")) == NULL ||
      (cms = d2i_CMS_bio(b, NULL)) == NULL)
    goto done;
  BIO_free(b);

  if (print_signerinfo) {
    STACK_OF(CMS_SignerInfo) *signerInfos = CMS_get0_SignerInfos(cms);
    STACK_OF(X509) *certs = CMS_get1_certs(cms);
    STACK_OF(X509_CRL) *crls = CMS_get1_crls(cms);
    printf("Certificates:   %d\n", certs ? sk_X509_num(certs) : 0);
    printf("CRLs:           %d\n", crls ? sk_X509_CRL_num(crls) : 0);
    for (i = 0; i < sk_CMS_SignerInfo_num(signerInfos); i++) {
      ASN1_OCTET_STRING *hash = NULL;
      printf("SignerId[%d]:    ", i);
      if (CMS_SignerInfo_get0_signer_id(sk_CMS_SignerInfo_value(signerInfos, i), &hash, NULL, NULL))
	for (j = 0; j < hash->length; j++)
	  printf("%02x%s", hash->data[j], j == hash->length - 1 ? "" : ":");
      else
	printf("[Could not read SID]");
      if (certs)
	for (j = 0; j < sk_X509_num(certs); j++)
	  if (!CMS_SignerInfo_cert_cmp(sk_CMS_SignerInfo_value(signerInfos, i), sk_X509_value(certs, j)))
	    printf(" [Matches certificate %d]", j);
      printf("\n");
    }
    sk_X509_pop_free(certs, X509_free);
    sk_X509_CRL_pop_free(crls, X509_CRL_free);
  }

  if (print_cms) {
    if ((b = BIO_new(BIO_s_fd())) == NULL)
      goto done;
    BIO_set_fd(b, 1, BIO_NOCLOSE);
    CMS_ContentInfo_print_ctx(b, cms, 0, NULL);
    BIO_free(b);
  }

  if ((b = BIO_new(BIO_s_mem())) == NULL ||
      CMS_verify(cms, NULL, NULL, NULL, b, CMS_NOCRL | CMS_NO_SIGNER_CERT_VERIFY | CMS_NO_ATTR_VERIFY | CMS_NO_CONTENT_VERIFY) <= 0 ||
      (r = ASN1_item_d2i_bio(ASN1_ITEM_rptr(ROA), b, NULL)) == NULL)
    goto done;

  if (print_roa) {

    if ((oid = CMS_get0_eContentType(cms)) == NULL)
      goto done;
    OBJ_obj2txt(buf, sizeof(buf), oid, 0);
    printf("eContentType:   %s\n", buf);

    if (r->version)
      printf("version:        %ld\n", ASN1_INTEGER_get(r->version));
    else
      printf("version:        0 [Defaulted]\n");
    printf("asID:           %ld\n", ASN1_INTEGER_get(r->asID));

    for (i = 0; i < sk_ROAIPAddressFamily_num(r->ipAddrBlocks); i++) {

      ROAIPAddressFamily *f = sk_ROAIPAddressFamily_value(r->ipAddrBlocks, i);

      unsigned afi = (f->addressFamily->data[0] << 8) | (f->addressFamily->data[1]);

      printf(" addressFamily: %x", afi);
      if (f->addressFamily->length == 3)
	printf("[%x]", f->addressFamily->data[2]);
      printf("\n");

      for (j = 0; j < sk_ROAIPAddress_num(f->addresses); j++) {
	ROAIPAddress *a = sk_ROAIPAddress_value(f->addresses, j);

	printf("     IPaddress: ", afi);

	switch (afi) {

	case IANA_AFI_IPV4:
	  addr_expand(addr, a->IPAddress, 4);
	  printf("%d.%d.%d.%d", addr[0], addr[1], addr[2], addr[3]);
	  break;

	case IANA_AFI_IPV6:
	  addr_expand(addr, a->IPAddress, 16);
	  for (n = 16; n > 1 && addr[n-1] == 0x00 && addr[n-2] == 0x00; n -= 2)
	    ;
	  for (k = 0; k < n; k += 2)
	    printf("%x%s", (addr[k] << 8) | addr[k+1], (k < 14 ? ":" : ""));
	  if (k < 16)
	    printf(":");
	  break;

	default:
	  for (k = 0; k < a->IPAddress->length; k++)
	    printf("%s%02x", (k > 0 ? ":" : ""), a->IPAddress->data[k]);
	  printf("[%d]", (int) (a->IPAddress->flags & 7));
	  break;

	}

	printf("/%u\n", addr_prefixlen(a->IPAddress));

	if (a->maxLength)
	  printf("-%ld", ASN1_INTEGER_get(a->maxLength));

	printf("\n");
      }
    }
  }

 done:
  if (ERR_peek_error())
    ERR_print_errors_fp(stderr);
  BIO_free(b);
  CMS_ContentInfo_free(cms);
  return r;
}



/*
 * Main program.
 */
int main (int argc, char *argv[])
{
  int result = 0;
  OpenSSL_add_all_algorithms();
  ERR_load_crypto_strings();
  while (--argc > 0)
    result |=  read_roa(*++argv, 0, 1, 1) == NULL;
  return result;
}
