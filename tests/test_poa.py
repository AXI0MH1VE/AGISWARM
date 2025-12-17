import nacl.signing
import nacl.encoding
from aggregator.poa_gate import PoAGate

def test_ed25519_verify():
    # Generate key
    sk = nacl.signing.SigningKey.generate()
    vk = sk.verify_key
    msg = b"test-msg"
    sig = sk.sign(msg).signature
    vk_hex = vk.encode(encoder=nacl.encoding.HexEncoder).decode()
    # Save key
    with open("/tmp/test_pubkey.txt", "w") as f:
        f.write(vk_hex)
    g = PoAGate("/tmp/test_pubkey.txt")
    assert g.verify(msg, sig, vk_hex)

