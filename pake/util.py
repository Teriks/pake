
class _ReadOnlyList:
    def __init__(self, l):
        self._l = l

    def __getitem__(self, item):
        return self._l[item]

    def __iter__(self):
        for i in self._l:
            yield i
