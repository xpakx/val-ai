import msgspec
import requests
from selectolax.parser import HTMLParser


class Link(msgspec.Struct):
    name: str
    link: str
    description: str


def search(query: str) -> list[Link]:
    """Search internet"""
    url = "https://lite.duckduckgo.com/lite/"
    headers = {"User-Agent": "Mozilla/5.0"}
    data = {"q": query}
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    tree = HTMLParser(response.text)

    link_nodes = tree.css(".result-link")
    snippet_nodes = tree.css(".result-snippet")
    links: list[Link] = []

    for link, snippet in zip(link_nodes, snippet_nodes):
        href = link.attributes.get("href")
        if not href:
            continue
        links.append(
            Link(
                name=link.text().strip(), link=href, description=snippet.text().strip()
            )
        )

    return links


if __name__ == "__main__":
    results = search("ai agents")
    for r in results:
        print(r.name)
        print(r.link)
        print(r.description)
        print()
