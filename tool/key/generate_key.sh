openssl ecparam -name secp256k1 -genkey -noout -out ec-secp256k1-private.pem
openssl ec -in  ec-secp256k1-private.pem -pubout -outform DER -out ec-secp256k1-public.der
dd if=ec-secp256k1-public.der of=ec-secp256k1-public-raw.bin bs=1 skip=24 count=64