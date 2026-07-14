import requests
from selectolax.parser import HTMLParser
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
    tree = HTMLParser(response.text)

    entries = tree.css('entry')
    links: list[ArXivData] = []

    for entry in entries:
        struct = ArXivData(categories=[], authors=[])
        # TODO: selectolax seems to be confused by self-closing tags
        for child in entry.iter():
            if child.tag == 'id':
                struct.id = child.text()
            elif child.tag == 'title':
                struct.title = child.text()
            elif child.tag == 'summary':
                struct.description = child.text()
            elif child.tag == 'link':
                tp = child.attributes.get('title')
                href = child.attributes.get('href')
                if tp == 'pdf':
                    struct.pdf_link = href
                else:
                    struct.html_link = href
            elif child.tag == 'published':
                struct.published = child.text()
            elif child.tag == 'arxiv:journal_ref':
                struct.journal = child.text()
            elif child.tag == 'author':
                struct.authors.append(child.first_child.text())
            elif child.tag == 'category':
                struct.categories.append(child.attributes.get('term'))
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
    r = results[0]
    arxiv_get_pdf(r, 'test.pdf')
