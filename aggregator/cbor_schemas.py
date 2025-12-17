import cbor2
import time

def pack_task(seq, tid, coeffs, x_fixed, coded_matrix=None):
    task = {
        "t": "TASK",
        "seq": seq,
        "tid": tid,
        "c": coeffs,
        "x": x_fixed,
        "ts": time.time_ns()
    }
    if coded_matrix is not None:
        task["M"] = coded_matrix
    return cbor2.dumps(task)

def pack_result(seq, tid, worker_id, y_fixed):
    return cbor2.dumps({
        "t": "RES",
        "seq": seq,
        "tid": tid,
        "w": worker_id,
        "y": y_fixed,
        "ts": time.time_ns()
    })

def pack_proposed_state(seq, x_next, conf):
    return cbor2.dumps({
        "t": "PROP",
        "seq": seq,
        "x": x_next,
        "conf": conf,
        "ts": time.time_ns()
    })

def pack_commit(seq, sig, pubkey):
    return cbor2.dumps({
        "t": "COMMIT",
        "seq": seq,
        "sig": sig,  # bytes
        "pk": pubkey
    })

