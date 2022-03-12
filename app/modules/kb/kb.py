from whoosh.fields import Schema, TEXT, KEYWORD, ID
from whoosh.analysis import StemmingAnalyzer
from whoosh import index
from whoosh.qparser import QueryParser
import os
import re
import json


TAG = re.compile(r"##([\w\s,]+)")


class KnowledgeBase:
    def __init__(self, directory, name="kb", clear=False):
        if not os.path.exists(directory):
            os.mkdir(directory)
        if not index.exists_in(directory, indexname=name) or clear:
            self._schema = Schema(
                title=ID(stored=True),
                path=ID,
                content=TEXT(analyzer=StemmingAnalyzer()),
                tags=KEYWORD(stored=True, scorable=True, lowercase=True, commas=True))
            self._index = index.create_in(
                directory, schema=self._schema, indexname=name)
        else:
            self._index = index.open_dir(directory, indexname=name)
            self._schema = self._index.schema
        self._searcher = None
        self._writer = None
        self._directory = directory
        self.indexed_files = self._load_filelist()

    def _load_filelist(self):
        pth = os.path.join(self._directory, "indexed.json")
        if os.path.exists(pth):
            result = {}
            with open(pth, "r", encoding="utf-8") as fobj:
                result = json.load(fobj)
            return result
        else:
            return {}

    def _dump_filelist(self):
        pth = os.path.join(self._directory, "indexed.json")
        with open(pth, "w", encoding="utf-8") as fobj:
            json.dump(self.indexed_files, fobj, ensure_ascii=False)

    def _is_new_in_index(self, path, mtime):
        if path in self.indexed_files:
            return self.indexed_files[path] != mtime
        else:
            return True

    def index_from_directory(self, directory):
        self._writer = self._index.writer()
        if os.path.exists(directory):
            files = os.listdir(directory)
            for file in files:
                pth = os.path.abspath(os.path.join(directory, file))
                mtime = os.path.getmtime(pth)
                if os.path.isfile(pth) and self._is_new_in_index(pth, mtime):
                    with open(pth, "r", encoding="utf-8") as fobj:
                        content = fobj.read()
                    tags = []
                    for i in re.findall(TAG, content):
                        for tag in i.strip().split(","):
                            tags.append(tag)
                    title = os.path.splitext(file)[0]
                    self.indexed_files[pth] = mtime
                    self._writer.add_document(
                        title=title, content=content, path=pth, tags=",".join(tags))
        self._writer.commit()
        self._writer = None
        self._dump_filelist()

    def open_indexer(self):
        if not self._writer:
            self._writer = self._index.writer()

    def close_indexer(self):
        if self._writer:
            self._writer.commit()
            self._writer = None

    def index(self, title, content, path, tags=[]):
        if self._writer:
            self._writer.add_document(
                title=title, content=content, path=path, tags=",".join(tags))

    def find(self, query, count=25, static_results=False):
        qp = QueryParser("content", schema=self._schema)
        q = qp.parse(query)
        self.start_search()
        results = self._searcher.search(q, limit=count)
        if not static_results:
            return results
        else:
            return freeze_results(results)

    def finish_search(self):
        if self._searcher:
            self._searcher.close()

    def start_search(self):
        if not self._searcher:
            self._searcher = self._index.searcher()


def freeze_results(results):
    static = list(map(dict, results))
    for i in range(len(static)):
        static[i]["score"] = results[i].score
        static[i]["pos"] = results[i].pos
        static[i]["rank"] = results[i].rank
    return static
