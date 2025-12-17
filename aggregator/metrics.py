import csv
import time

class MetricsLogger:
    def __init__(self, filename="metrics.csv"):
        self.f = open(filename, "w", newline='')
        self.writer = csv.writer(self.f)
        self.writer.writerow(["seq", "t_start", "t_comp_est", "t_comm_est", "t_agg", "t_cycle_total"])
        
    def log(self, seq, start, t_cycle):
        self.writer.writerow([seq, start, 0, 0, 0, t_cycle])
        self.f.flush()

