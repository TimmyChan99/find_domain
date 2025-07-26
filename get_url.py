from http.client import responses

import requests
from termcolor import cprint, colored
from urllib.parse import urlparse
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException


def find_active_domain(
    base_name: str, start_num: int, end_num: int, tld: str, timeout: int = 5
):
    cprint(
        f"Searching for active domain from {base_name}{start_num}{tld} to {base_name}{end_num}{tld}",
        "blue",
        attrs=["bold"],
    )

    for i in range(start_num, end_num + 1):
        initial_domain_str = f"{base_name}{i}{tld}"
        initial_url = f"http://{initial_domain_str}"

        cprint(f"checking {initial_domain_str}", "yellow")

        try:
            response = requests.get(initial_url, timeout=timeout, allow_redirects=True)

            if response.status_code == 200:
                final_url = response.url
                netloc = urlparse(final_url).netloc

                # Normalizing netloc
                final_netloc_normalized = netloc.replace("www", "")
                initial_netloc_normalized = urlparse(initial_url).netloc.replace(
                    "www", ""
                )

                is_same_domain = (
                    initial_netloc_normalized.lower() == final_netloc_normalized.lower()
                )

                if is_same_domain:

                    # Get page content
                    try:
                        content_simple = response.text[:5000]

                        if not content_simple.strip():
                            cprint(f"{final_url} has no content", "red")
                            continue

                        detected_lang = detect(content_simple)
                        if detected_lang == "ko":
                            cprint(
                                f"Found active, relevant, and Korean domain: {final_url}",
                                "green",
                            )
                            break
                        else:
                            cprint(
                                f"  {initial_url} is active and relevant, but content is in '{detected_lang}' (expected 'ko'). {colored('Skipping.', 'yellow')}"
                            )

                    except LangDetectException:
                        print(
                            f"  Could not detect language for {initial_url} (content too short or ambiguous). {colored('Skipping.', 'yellow')}"
                        )

                else:
                    print(
                        f"{initial_url} redirected to an unrelated domain: {final_url}. ",
                        colored("Skipping"),
                    )

            else:
                print(
                    f"  {initial_url} returned status code: {response.status_code}. ",
                    colored("Skipping"),
                )

        except requests.exceptions.ConnectionError:
            print(f"  Could not connect to {initial_url} (Connection Error). {colored("Skipping")}")

        except requests.exceptions.Timeout:
            print(
                f"  Request to {initial_url} timed out after {timeout} seconds. {colored("Skipping")}"
            )

        except requests.exceptions.RequestException as e:
            print(f"  An unexpected error occurred with {initial_url}: {e}. {colored("Skipping")}")

        except Exception as e:
            print(f"  An unhandled error occurred: {e}. {colored("Skipping")}")


if __name__ == "__main__":
    base_domain = "site"
    start_number = 325
    end_number = 700
    tld_extension = ".com"

    find_active_domain(base_domain, start_number, end_number, tld_extension)
