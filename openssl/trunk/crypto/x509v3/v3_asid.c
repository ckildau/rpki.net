/* v3_asid.c */

/* $Id$ */
/*
 * Initial attempt to implement RFC 3779 section 3.  I'd be very
 * surprised if this even compiled yet, as I'm still figuring out
 * OpenSSL's ASN.1 template goop.
 */

#include <stdio.h>
#include "cryptlib.h"
#include <openssl/conf.h>
#include <openssl/asn1.h>
#include <openssl/asn1t.h>
#include <openssl/x509v3.h>

/* RFC 3779 AS ID */

ASN1_SEQUENCE(ASRange) = {
	ASN1_SIMPLE(ASRange, min, ASN1_INTEGER),
	ASN1_SIMPLE(ASRange, max, ASN1_INTEGER)
} ASN1_SEQUENCE_END(ASRange)

ASN1_CHOICE(ASIdOrRange) = {
	ASN1_SIMPLE(ASIdOrRange, u.id, ASN1_INTEGER),
	ASN1_SIMPLE(ASIdOrRange, u.range, ASRange)
} ASN1_CHOICE_END(ASIdOrRange)

ASN1_CHOICE(ASIdentiferChoice) = {
	ASN1_IMP(ASIdentiferChoice, u.inherit, ASN1_NULL),
	ASN1_IMP_SEQUENCE_OF(ASIdentiferChoice, u.asIdsOrRanges, ASIdOrRange)
} ASN1_CHOICE_END(ASIdentiferChoice)

ASN1_SEQUENCE(ASIdentifiers) = {
	ASN1_EXP_OPT(ASIdentifiers, asnum, ASIdentiferChoice, 0),
	ASN1_EXP_OPT(ASIdentifiers, rdi, ASIdentiferChoice, 1)
} ASN1_SEQUENCE_END(ASIdentifiers)

IMPLEMENT_ASN1_FUNCTIONS(ASRange)
IMPLEMENT_ASN1_FUNCTIONS(ASIdOrRange)
IMPLEMENT_ASN1_FUNCTIONS(ASIdentiferChoice)
IMPLEMENT_ASN1_FUNCTIONS(ASIdentifiers)

static int i2r_ASIdentifierChoice(BIO *out,
				  ASIdentiferChoice *choice,
				  int indent,
				  const char *msg)
{
  int i;
  char *s;
  if (choice == NULL)
    return 1;
  BIO_printf(out, "%*s%s: ", indent, "", msg);
  switch (choice->type) {
  case ASIdentifierChoice_inherit:
    BIO_puts(out, "inherit");
    break;
  case ASIdentifierChoice_asIdsOrRanges:
    for (i = 0; i < sk_ASIdOrRange_num(choice->u.asIdsOrRanges); i++) {
      ASIdOrRange aor = sk_ASIdOrRange_num(choice->u.asIdsOrRanges, i);
      if (i > 0)
	BIO_puts(out, ", ");
      switch (aor->type) {
      case ASIdOrRange_id:
	if ((s = i2s_ASN1_INTEGER(NULL, aor->u.id)) == NULL)
	  return 0;
	BIO_puts(out, s);
	OPENSSL_free(s);
	break;
      case ASIdOrRange_range:
	if ((s = i2s_ASN1_INTEGER(NULL, aor->u.range->min)) == NULL)
	  return 0;
	BIO_puts(out, s);
	OPENSSL_free(s);
	BIO_puts(out, " - ");
	if ((s = i2s_ASN1_INTEGER(NULL, aor->u.range->max)) == NULL)
	  return 0;
	BIO_puts(out, s);
	OPENSSL_free(s);
	break;
      default:
	return 0;
      }
    }
    break;
  default:
    return 0;
  }
  BIO_puts(out, "\n");
  return 1;
}

static int i2r_ASIdentifiers(X509V3_EXT_METHOD *method,
			     void *ext,
			     BIO *out,
			     int indent)
{
  ASIdentifiers *asid = ext;
  return (i2r_ASIdentifierChoice(out, asid->asnum, indent, "Autonomous System Numbers") &&
	  i2r_ASIdentifierChoice(out, asid->rdi,   indent, "Routing Domain Identifiers"));
}

static void *v2i_ASIdentifiers(struct v3_ext_method *method,
			       struct v3_ext_ctx *ctx,
			       STACK_OF(CONF_VALUE) *values)
{
  ASIdentifiers *asid = NULL;
  CONF_VALUE *val;
  int i;

  if ((asid = ASIdentifiers_new()) == NULL) {
    X509V3err(X509V3_F_V2I_ASIdentifiers, ERR_R_MALLOC_FAILURE);
    return NULL;
  }

#error not written yet

  /*
   * Need to:
   * - Read stuff from config
   * - Sort/merge/canonicalize
   * - Generate and return C structure
   */

  return result;
}

X509V3_EXT_METHOD v3_asid = {
  NID_ASIdentifiers,		/* nid */
  0,				/* flags */
  ASN1_ITEM_ref(ASIdentifiers),	/* template */
  0, 0, 0, 0,			/* old functions, ignored */
  0,				/* i2s */
  0,				/* s2i */
  0,				/* i2v */
  v2i_ASIdentifiers,		/* v2i */
  i2r_ASIdentifiers,		/* i2r */
  0,				/* r2i */
  NULL				/* extension-specific data */
};
