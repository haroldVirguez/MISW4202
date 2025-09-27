from jwcrypto import jwk
import json

# Generate an RSA key
key = jwk.JWK.generate(kty='RSA', size=2048)

# Set a unique Key ID (kid)
key.kid = "1234"

# Export the key as JWKS
jwks = {"keys": [json.loads(key.export_public())]}

# Save the JWKS to a file
with open("jwks.json", "w") as jwks_file:
    json.dump(jwks, jwks_file, indent=4)

print("JWKS generated and saved to jwks.json")