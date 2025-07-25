
import os
import time


class _TIMESTAMP:
    def __init__(self):
        self.timestamps = []
        self.add_start_timestamp()

    def __call__(self, label):
        self.timestamps.append(self.timestamp(label))

    def add_start_timestamp(self):
        start_timestamp = os.environ.get('EZAZ_START_TIMESTAMP')
        if start_timestamp:
            self.timestamps.append(('start', float(start_timestamp)))
        else:
            self.timestamp('start')

    def timestamp(self, label):
        return (label, time.perf_counter())

    def label_width(self, *labels):
        return max(*map(len, labels))

    def show(self, dest=None):
        if not self.timestamps:
            return

        end = self.timestamp('end')

        width = self.label_width(*map(lambda i: i[0], self.timestamps), 'end', 'total')

        start = last = self.timestamps[0][1]
        for label, ts in self.timestamps:
            last = self.show_timestamp(last, ts, label, width, dest=dest)
        self.show_timestamp(last, end[1], end[0], width, dest=dest)

        print(file=dest)
        self.show_timestamp(start, end[1], 'total', width, dest=dest)

    def show_timestamp(self, start, end, label, label_width, dest=None):
        delta = round(end - start, 6)
        print(f'{label:{label_width}} : +{delta:09.6f}s', file=dest)
        return end


TIMESTAMP = _TIMESTAMP()
