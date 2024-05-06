import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
from postgrest.types import ReturnMethod
from postgrest import APIResponse

# Load environment variables from .env file
load_dotenv()

from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)


def fetch_mime_types_and_extensions(url: str) -> list:
    """
    Fetch MIME types and their extensions from the specified URL using BeautifulSoup.

    Returns a list of dictionaries with 'mime' and 'extensions' keys.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    mime_types_data = []

    # Assuming the structure of the page has a table where MIME types and extensions are in <td> tags
    # Typically, the first <td> would be the MIME type and the second <td> could contain the extensions
    for row in soup.find_all("tr"):
        cols = row.find_all("td")
        # Ensure the row has at least two columns (for MIME type and extensions)
        if len(cols) >= 2:
            mime_type = cols[0].text.strip()
            # Assuming extensions are comma-separated in the second <td>
            extensions = cols[1].text.strip().split(", ")
            mime_types_data.append({"mime": mime_type, "extensions": extensions})

    return mime_types_data


def generate_readable_name(mime_type: str) -> str:
    """
    Generate a human-readable name for a MIME type using GPT-4.
    """
    prompt = f"Convert the MIME type '{mime_type}' into a human-readable name and return only the canonical name itself."
    response = client.chat.completions.create(
        model="gpt-4-turbo",  # Updated model name
        messages=[{"role": "system", "content": "You are a helpful assistant that understands MIME types."},
                  {"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=60,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        stop=["\n"]
    )
    return response.choices[0].message.content.strip()


def main():
    url = "https://mimetype.io/all-types"
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")

    # Initialize Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)

    mime_types = fetch_mime_types_and_extensions(url)

    for mime_type in mime_types:
        readable_name = generate_readable_name(mime_type)
        # Insert into Supabase database
        data = {
            "mime": mime_type.get("mime"),
            "name": readable_name,
            "extensions": mime_type.get("extensions"),
        }
        return_method: ReturnMethod = ReturnMethod.representation
        response: APIResponse = supabase.table("mime_type").insert(
            json=data,
            upsert=True,
            returning=return_method
        ).execute()

        if response.data is not None:
            print(f"Successfully inserted {data.get("mime")}")
        else:
            print(f"Failed to insert {mime_type}")


if __name__ == "__main__":
    main()
