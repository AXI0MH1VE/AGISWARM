import nacl.signing
import nacl.encoding

class PoAGate:
    def __init__(self, authorized_keys_file):
        self.verifying_keys = []
        try:
            with open(authorized_keys_file, 'r') as f:
                for line in f:
                    hex_key = line.strip()
                    if hex_key:
                        self.verifying_keys.append(
                            nacl.signing.VerifyKey(hex_key, encoder=nacl.encoding.HexEncoder)
                        )
        except FileNotFoundError:
            print("WARNING: No authorized keys found. PoA will fail.")

    def verify(self, message_bytes, signature_bytes, pubkey_hex):
        vk = next((k for k in self.verifying_keys 
                   if k.encode(nacl.encoding.HexEncoder).decode() == pubkey_hex), None)
        if not vk:
            return False
        try:
            vk.verify(message_bytes, signature_bytes)
            return True
        except nacl.exceptions.BadSignatureError:
            return False

