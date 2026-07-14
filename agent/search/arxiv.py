import requests
import pygixml
import msgspec
from pathlib import Path


class ArXivData(msgspec.Struct):
    id: str = ""
    title: str = ""
    description: str = ""
    html_link: str | None = None
    pdf_link: str | None = None
    published: str | None = None
    journal: str | None = None
    categories: list[str] | None = None
    authors: list[str] | None = None


def search_arxiv(query: str) -> list[ArXivData]:
    url = "http://export.arxiv.org/api/query"
    data = {"search_query": f"all:{query}"}

    response = requests.get(url, params=data)
    response.raise_for_status()
    tree = pygixml.parse_string(response.text)

    entries = tree.root.select_nodes('entry')
    links: list[ArXivData] = []

    for entry in entries:
        struct = ArXivData(categories=[], authors=[])
        for child in entry.node.children():
            if child.name == 'id':
                struct.id = child.text()
            elif child.name == 'title':
                struct.title = child.text()
            elif child.name == 'summary':
                struct.description = child.text()
            elif child.name == 'link':
                tp = child.attribute('title').value
                href = child.attribute('href').value
                if tp == 'pdf':
                    struct.pdf_link = href
                else:
                    struct.html_link = href
            elif child.name == 'published':
                struct.published = child.text()
            elif child.name == 'arxiv:journal_ref':
                struct.journal = child.text()
            elif child.name == 'author':
                struct.authors.append(child.first_child().text())
            elif child.name == 'category':
                struct.categories.append(child.attribute('term').value)
        links.append(struct)
    return links


def arxiv_get_pdf(paper: ArXivData, output: str | Path):
    if not paper.pdf_link:
        return
    output = Path(output)

    with (
            requests.get(paper.pdf_link, stream=True) as response,
            output.open("wb") as f,
    ):
        response.raise_for_status()

        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)


if __name__ == "__main__":
    results = search_arxiv("agents")
    for r in results:
        print(r)
        print()
    exit(0)
    r = results[0]
    arxiv_get_pdf(r, 'test.pdf')
