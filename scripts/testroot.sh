#!/bin/sh -
# $Id$
#
# Script to test against testroot.py.
#
# This blows away rpkid's database and rebuilds it with what we need
# for this test, and knows far too much about the id numbers that
# rpkid and mysql will assign.  In the long run we must do better than
# this, but gotta start somewhere.

openssl=../openssl/openssl/apps/openssl

# Generate new key and cert for testroot.py if needed

if test ! -r testroot.cer -o ! -r testroot.key
then
  $openssl req -new -newkey rsa:2048 -nodes -keyout testroot.key -out testroot.req -config testroot.cnf
  $openssl x509 -req -in testroot.req -out testroot.cer -extfile testroot.cnf -extensions req_x509_ext -signkey testroot.key -text -sha256
  rm -f testroot.req
fi

# Blow away old rpkid database (!) so we can start clean

mysql -u rpki -p`awk '$1 == "sql-password" {print $3}' rpkid.conf` rpki <../docs/rpki-db-schema.sql

# Start rpkid so we can configure it

python rpkid.py & rpkid=$!

# Create a self instance

python irbe-cli.py self --action create

# Create a business signing context, issue the necessary business cert, and set up the cert chain

python irbe-cli.py --pem_out bsc.req bsc --action create --self_id 1 --generate_keypair --signing_cert biz-certs/Bob-CA.cer
$openssl x509 -req -in bsc.req -out bsc.cer -CA biz-certs/Bob-CA.cer -CAkey biz-certs/Bob-CA.key -CAserial biz-certs/Bob-CA.srl
python irbe-cli.py bsc --action set --self_id 1 --bsc_id 1 --signing_cert bsc.cer
rm -f bsc.req bsc.cer

# Create a repository context

python irbe-cli.py repository --self_id 1 --action create --bsc_id 1

# Create a parent context pointing at testroot.py

python irbe-cli.py parent --self_id 1 --action create --bsc_id 1 --repository_id 1 \
    --peer_contact_uri https://localhost:44333/ \
    --cms_ta biz-certs/Elena-Root.cer \
    --https_ta biz-certs/Elena-Root.cer 

# Shut down rpkid (there should be a left-right command for this!)

kill $rpkid
