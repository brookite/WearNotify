def dummy(*args, **kwargs):
    # empty function
    pass


class ChapteredText:
    def __init__(self, text):
        self._chapters = {"Header": ""}
        current = "Header"
        for line in text.split("\n"):
            if line.startswith("=="):
                current = line[2:]
                if current not in self._chapters:
                    self._chapters[current] = ""
            else:
                self._chapters[current] += line + "\n"
    
    def chapters(self):
        return tuple(self._chapters.keys())
    
    def get(self, chapter):
        if isinstance(chapter, int):
            chapter = self.chapters()[chapter]
        return self._chapters.get(chapter)
