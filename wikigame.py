import requests
import time
import random
import urllib.parse
from collections import deque

API_URL = "https://de.wikipedia.org/w/api.php"

session = requests.Session()
session.headers.update({
    "User-Agent": "WikiPathFinder/bidirectional-heuristic"
})

MIN_DELAY = 0.4
MAX_DELAY = 1.2

FORWARD_TOP_N = 25
BACKWARD_TOP_N = 10
MAX_DEPTH = 6


def clean_input(text):
    text = text.strip()
    if "wikipedia.org/wiki/" in text:
        text = text.split("/wiki/")[1]
    return urllib.parse.unquote(text)


def normalize(title):
    return title.strip().replace(" ", "_")


def sleep():
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    if random.random() < 0.1:
        time.sleep(random.uniform(2, 4))


def get_links(title):
    links = set()

    params = {
        "action": "query",
        "format": "json",
        "titles": title,
        "prop": "links",
        "pllimit": "max"
    }

    while True:
        sleep()
        try:
            r = session.get(API_URL, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"Fehler bei {title}: {e}")
            return links

        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            for link in page.get("links", []):
                links.add(link["title"])

        if "continue" in data:
            params.update(data["continue"])
        else:
            break

    return links


def score(link, target_words):
    words = set(link.lower().replace("_", " ").split())
    return len(words & target_words)


def sort_links(links, target_words):
    return sorted(
        links,
        key=lambda l: score(l, target_words),
        reverse=True
    )


def bidirectional_search(start, target):
    target_words = set(target.lower().replace("_", " ").split())

    forward_queue = deque([(start, [start], 0)])
    backward_queue = deque([(target, [target], 0)])

    forward_visited = {start: None}
    backward_visited = {target: None}

    while forward_queue and backward_queue:

        if len(forward_queue) <= len(backward_queue):

            current, path, depth = forward_queue.popleft()

            print(f"Forward: {current} (Tiefe {depth})")

            if depth >= MAX_DEPTH:
                continue

            links = get_links(current)
            links = sort_links(links, target_words)[:FORWARD_TOP_N]

            for link in links:
                if link in forward_visited:
                    continue

                forward_visited[link] = current
                new_path = path + [link]

                if link in backward_visited:
                    return build_path(link, forward_visited, backward_visited)

                forward_queue.append((link, new_path, depth + 1))

        else:

            current, path, depth = backward_queue.popleft()

            print(f"Backward: {current} (Tiefe {depth})")

            if depth >= MAX_DEPTH:
                continue

            links = get_links(current)
            links = sort_links(links, target_words)[:BACKWARD_TOP_N]

            for link in links:
                if link in backward_visited:
                    continue

                backward_visited[link] = current
                new_path = path + [link]

                if link in forward_visited:
                    return build_path(link, forward_visited, backward_visited)

                backward_queue.append((link, new_path, depth + 1))

    return None


def build_path(meeting, forward_visited, backward_visited):
    path = []

    node = meeting
    while node:
        path.append(node)
        node = forward_visited.get(node)
    path.reverse()

    node = backward_visited.get(meeting)
    while node:
        path.append(node)
        node = backward_visited.get(node)

    return path


if __name__ == "__main__":
    print("Wikipedia Bidirectional Smart Pathfinder")

    start = normalize(clean_input(input("Start: ")))
    target = normalize(clean_input(input("Ziel: ")))

    print(f"\nSuche von {start} -> {target}\n")

    result = bidirectional_search(start, target)

    if result:
        print("\nGefundener Pfad:")
        for step in result:
            print("-> https://de.wikipedia.org/wiki/" + step)
    else:
        print("Kein Pfad gefunden")
