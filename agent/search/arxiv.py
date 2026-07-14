import requests
from selectolax.parser import HTMLParser
import msgspec


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

    response = requests.get(url, data)
    response.raise_for_status()
    tree = HTMLParser(response.text)

    entries = tree.css('entry')
    links: list[ArXivData] = []

    for entry in entries:
        struct = ArXivData(categories=[], authors=[])
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
                struct.authors.append(child.text())
            elif child.tag == 'category':
                struct.authors.append(child.attributes.get('term'))
        links.append(struct)
    return links


if __name__ == "__main__":
    results = search_arxiv("agents")
    print(results[0])
