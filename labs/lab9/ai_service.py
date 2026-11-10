import os

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from pydantic import BaseModel

load_dotenv()


class ProjectDetails(BaseModel):
    title: str
    summary: str
    technologies: list[str]


class ModelRefusalError(Exception):
    pass


class ProviderUnavailableError(Exception):
    pass


api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None


def extract_project_details(notes: str) -> ProjectDetails:
    if client is None:
        raise ProviderUnavailableError("The AI provider is not configured")

    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract a concise project title, a one- or two-sentence "
                        "summary, and a list of technologies from the user's notes."
                    ),
                },
                {"role": "user", "content": notes},
            ],
            response_format=ProjectDetails,
            temperature=0.1,
        )
    except OpenAIError as error:
        raise ProviderUnavailableError("The AI provider is unavailable") from error

    message = completion.choices[0].message
    if message.refusal:
        raise ModelRefusalError("The AI model refused to process these notes")
    if message.parsed is None:
        raise RuntimeError("The AI provider returned no project details")

    return message.parsed
