from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = {"index.html", "corpus.html", "data/Itelmen_dict.csv"}
PUBLIC.update(p.relative_to(ROOT).as_posix() for p in (ROOT / "assets").glob("*") if p.suffix in {".js", ".css"})

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_head(self):
        path = unquote(urlsplit(self.path).path)
        if path != "/" and path[1:] not in PUBLIC:
            return self.send_error(404)
        return super().send_head()

if __name__ == "__main__":
    print("http://127.0.0.1:8766/", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8766), Handler).serve_forever()
