import nacl.signing
import nacl.encoding

# Generate Keypair
signing_key = nacl.signing.SigningKey.generate()
verify_key = signing_key.verify_key

sk_hex = signing_key.encode(encoder=nacl.encoding.HexEncoder).decode()
vk_hex = verify_key.encode(encoder=nacl.encoding.HexEncoder).decode()

print(f"Private Key: {sk_hex}")
print(f"Public Key:  {vk_hex}")

# Save for usage
with open("operator.sk", "w") as f: f.write(sk_hex)
with open("authorized_keys.txt", "w") as f: f.write(vk_hex)
print("Keys saved.")

