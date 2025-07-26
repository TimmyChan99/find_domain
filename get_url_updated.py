import requests
from requests.exceptions import RequestException
import time
import urllib.parse
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Set a seed for reproducibility in language detection (optional)
DetectorFactory.seed = 0


def find_active_domain(base_name: str, start_num: int, end_num: int, tld: str, timeout: int = 5) -> str | None:

    print(f"Searching for active domain from {base_name}{start_num}{tld} to {base_name}{end_num}{tld}...")

    for i in range(start_num, end_num + 1):
        initial_domain_str = f"{base_name}{i}{tld}"
        initial_url = f"http://{initial_domain_str}"  # Try HTTP first
        print(f"Checking {initial_url}...")
        try:
            # Send a GET request to the URL with a timeout
            # allow_redirects=True is kept to follow HTTP to HTTPS redirects,
            # but we will verify the final URL's domain.
            response = requests.get(initial_url, timeout=timeout, allow_redirects=True)

            # Check if the status code indicates success (200 OK)
            if response.status_code == 200:
                final_url = response.url

                # Extract the netloc (domain part) from the initial and final URLs
                # Use urlparse to handle potential variations in URL structure (e.g., with/without www, paths)
                initial_netloc = urllib.parse.urlparse(initial_url).netloc
                final_netloc = urllib.parse.urlparse(final_url).netloc

                # Normalize netlocs by removing 'www.' for comparison if present
                initial_netloc_normalized = initial_netloc.replace('www.', '')
                final_netloc_normalized = final_netloc.replace('www.', '')

                # Check if the final URL's domain is the same as the initial domain (ignoring www. and protocol)
                is_same_domain = initial_netloc_normalized.lower() == final_netloc_normalized.lower()

                if is_same_domain:
                    # If it's the same domain (or www. variant), and the base_name is still in the final URL, it's valid.
                    if base_name.lower() in final_url.lower():
                        # --- NEW: Language detection ---
                        try:
                            # Take a sample of the content to detect language efficiently
                            # Using response.text ensures proper decoding based on content-type header
                            content_sample = response.text[:5000]  # Use first 5KB of text for detection
                            if not content_sample.strip():  # Check if content_sample is empty or just whitespace
                                print(f"  {initial_url} has no detectable text content for language check. Skipping.")
                                continue  # Skip to next domain if no content

                            detected_lang = detect(content_sample)
                            if detected_lang == 'ko':
                                print(f"Found active, relevant, and Korean domain: {final_url}")
                                return final_url
                            else:
                                print(
                                    f"  {initial_url} is active and relevant, but content is in '{detected_lang}' (expected 'ko'). Skipping.")
                        except LangDetectException:
                            print(
                                f"  Could not detect language for {initial_url} (content too short or ambiguous). Skipping.")
                        except Exception as lang_e:
                            print(
                                f"  An error occurred during language detection for {initial_url}: {lang_e}. Skipping.")
                        # --- END NEW ---
                    else:
                        print(
                            f"  {initial_url} is active but final URL '{final_url}' does not contain '{base_name}'. Skipping.")
                else:
                    # It redirected to a different domain. This is considered an unrelated redirect.
                    print(f"  {initial_url} redirected to an unrelated domain: {final_url}. Skipping.")

            else:
                print(f"  {initial_url} returned status code: {response.status_code}. Skipping.")

        except requests.exceptions.ConnectionError:
            print(f"  Could not connect to {initial_url} (Connection Error). Skipping.")
        except requests.exceptions.Timeout:
            print(f"  Request to {initial_url} timed out after {timeout} seconds. Skipping.")
        except RequestException as e:
            print(f"  An unexpected error occurred with {initial_url}: {e}. Skipping.")
        except Exception as e:
            print(f"  An unhandled error occurred: {e}. Skipping.")

        # Optional: Add a small delay between requests to avoid overwhelming servers
        time.sleep(0.1)

    print("No active, relevant, and Korean-language domain found within the specified range.")
    return None


# --- Example Usage ---
if __name__ == "__main__":
    base_domain = "site"
    start_number = 325
    end_number = 700
    tld_extension = ".com"

    found_url = find_active_domain(base_domain, start_number, end_number, tld_extension)

    if found_url:
        print(f"\nSuccessfully found the active and relevant domain: {found_url}")
    else:
        print("\nFailed to find an active and relevant domain.")

