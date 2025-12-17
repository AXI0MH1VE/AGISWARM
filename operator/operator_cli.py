import time
import json
import nacl.signing
import nacl.encoding
import socket
import cbor2
import os

def main():
    # Load Key
    with open("operator.sk", "r") as f:
        sk_hex = f.read().strip()
    signing_key = nacl.signing.SigningKey(sk_hex, encoder=nacl.encoding.HexEncoder)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    last_seq = -1
    
    print("--- Edge-Lattice Operator Console ---")
    print("Waiting for proposed states...")
    
    while True:
        try:
            if not os.path.exists("proposed_state.json"):
                time.sleep(0.1)
                continue
                
            with open("proposed_state.json", "r") as f:
                state = json.load(f)
            
            if state['seq'] <= last_seq:
                time.sleep(0.1)
                continue
                
            print(f"\n[Cycle {state['seq']}] Proposed State x: {state['x'][:3]}...")
            print("Press ENTER to Sign & Commit (or Ctrl-C to abort)...")
            # In auto/demo, just sign quickly
            time.sleep(0.05)
            
            # Sign
            msg = str(state['seq']).encode()
            sig = signing_key.sign(msg).signature
            
            payload = {
                "t": "COMMIT",
                "seq": state['seq'],
                "sig": sig,
                "pk": signing_key.verify_key.encode(encoder=nacl.encoding.HexEncoder).decode()
            }
            
            sock.sendto(cbor2.dumps(payload), ("127.0.0.1", 6000))
            print(">>> Commit Sent.")
            last_seq = state['seq']
            
        except Exception as e:
            print(e)
            time.sleep(1)

if __name__ == "__main__":
    main()

