"""One read-only view over several .bamod files (Lateralus 24 Nov 2026 21:4x: "I don't think we need the complete file anymore", "yes ok get rid of it").
A gameplay build no longer writes the 12.9 GB complete package; the checks that read both the data and the models open
'GAMEPLAY.bamod+ASSETS.bamod'. A name found in more than one file is read from the first (the gameplay package)."""
import zipfile


class Union:
    def __init__(self, paths):
        self.zips = [zipfile.ZipFile(p) for p in paths]
        self.idx = {}
        for z in self.zips:
            for i in z.infolist():
                self.idx.setdefault(i.filename, (z, i))

    def namelist(self): return list(self.idx)
    def infolist(self): return [i for _, i in self.idx.values()]
    def getinfo(self, n): return self.idx[n][1]
    def read(self, n): return self.idx[n][0].read(n)
    def open(self, n, *a, **k): return self.idx[n][0].open(n, *a, **k)
    def close(self):
        for z in self.zips: z.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.close()


def open_package(arg):
    """A single .bamod path, or several joined with '+'."""
    parts = str(arg).split('+')
    return zipfile.ZipFile(parts[0]) if len(parts) == 1 else Union(parts)
