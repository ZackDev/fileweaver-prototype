class FileHandler:
    def __init__(self, file):
        self.file = file
        self.char = []
        self.unique = []
        self.buckets = {}
        try:
            self.read_document_char_by_char()
            self.unique_characters()
            self.fill_buckets()
        except Exception as e:
            print(f'client: filehandler error:\n{e}')
            print('client: exiting now.')
            exit(0)

    def read_document_char_by_char(self):
        length = 0
        with open(self.file, 'rb') as f:
            while True:
                c = f.read(1)
                if not c:
                    self.length = length
                    break
                length += 1
                self.char.append(c)

    def unique_characters(self):
        for c in self.char:
            try:
                self.unique.index(c)
            except Exception:
                self.unique.append(c)

    def fill_buckets(self):
        for u in self.unique:
            self.buckets[u] = []
            i = 0
            for c in self.char:
                if u == c:
                    self.buckets[u].append(i)
                i += 1


def test():
    f = FileHandler('input.txt')
    print(f.unique)
    print(f.buckets)


if __name__ == '__main__':
    test()
