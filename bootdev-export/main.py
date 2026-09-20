import os
from datetime import datetime
from pathlib import Path

import httpx

BASE_URL = "https://api.boot.dev/v1"
INDEX_PATH = "/spellbooks"
PAGE_PATH = "/spellbooks/{id}"

DEST_DIR = Path("data")


def _client() -> httpx.Client:
    token = os.environ.get("BOOTDEV_TOKEN")

    if token is None:
        raise RuntimeError("BOOTDEV_TOKEN must be set")

    return httpx.Client(base_url=BASE_URL, headers={"authorization": f"Bearer {token}"})


def fetch_spellbooks(client: httpx.Client):
    response = client.get(INDEX_PATH)
    response.raise_for_status()
    return response.json()


def fetch_spellbook_by_id(client: httpx.Client, id: str):
    response = client.get(f"{INDEX_PATH}/{id}")
    response.raise_for_status()
    return response.json()


def create_export_dir(root: Path = DEST_DIR) -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out = root / stamp
    out.mkdir(parents=True, exist_ok=True)
    return out


def main():
    DEST_DIR.mkdir(exist_ok=True)

    try:
        out = create_export_dir()

        with _client() as client:
            spellbooks = fetch_spellbooks(client)

            for spell in spellbooks[:2]:
                lesson_id = spell.get("lessonUUID", None)

                if not lesson_id:
                    continue

                spellbook_content = fetch_spellbook_by_id(client, lesson_id)
                course_title, chapter_title, lesson_title, content = (
                    spellbook_content["courseTitle"],
                    spellbook_content["chapterTitle"],
                    spellbook_content["lessonTitle"],
                    spellbook_content["entry"],
                )

                lesson_spell_path = (
                    out / course_title / chapter_title / f"{lesson_title}.md"
                )
                lesson_spell_path.parent.mkdir(parents=True, exist_ok=True)
                lesson_spell_path.write_text(content, encoding="utf-8")

    except httpx.RequestError as exc:
        print(f"An error occurred while requesting {exc.request.url!r}.")
    except httpx.HTTPStatusError as exc:
        print(
            f"Error response {exc.response.status_code} while requesting {exc.request.url!r}."
        )


if __name__ == "__main__":
    main()
