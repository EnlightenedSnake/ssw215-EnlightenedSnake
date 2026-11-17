import os
import uuid
from typing import Literal, TypedDict

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from pydantic import BaseModel, Field

load_dotenv()


class ProjectDetails(BaseModel):
    title: str
    summary: str
    technologies: list[str]


class GitHubProjectDraft(BaseModel):
    title: str = Field(description="A short project title")
    summary: str = Field(description="A one- or two-sentence project summary")
    technologies: list[str]
    difficulty: Literal["Beginner", "Intermediate", "Advanced"]


class GitHubSession(TypedDict):
    draft: GitHubProjectDraft
    messages: list[dict[str, str]]


class ModelRefusalError(Exception):
    pass


class ProviderUnavailableError(Exception):
    pass


class SessionNotFoundError(Exception):
    pass


api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None
github_sessions: dict[str, GitHubSession] = {}


def _request_github_draft(messages: list[dict[str, str]]) -> GitHubProjectDraft:
    if client is None:
        raise ProviderUnavailableError("The AI provider is not configured")

    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=messages,
            response_format=GitHubProjectDraft,
            temperature=0.1,
        )
    except OpenAIError as error:
        raise ProviderUnavailableError("The AI provider is unavailable") from error

    message = completion.choices[0].message
    if message.refusal:
        raise ModelRefusalError("The AI model refused to process this project")
    if message.parsed is None:
        raise RuntimeError("The AI provider returned no project draft")

    return message.parsed


def start_github_session(readme: str) -> tuple[str, GitHubProjectDraft]:
    session_id = str(uuid.uuid4())
    messages = [
        {
            "role": "system",
            "content": (
                "Create a concise project draft from the supplied project text. "
                "Return a short title, a one- or two-sentence summary, a list of "
                "technologies, and a difficulty of exactly Beginner, "
                "Intermediate, or Advanced."
            ),
        },
        {"role": "user", "content": readme},
    ]
    draft = _request_github_draft(messages)
    messages.append({"role": "assistant", "content": draft.model_dump_json()})
    github_sessions[session_id] = {"draft": draft, "messages": messages}
    return session_id, draft


def get_github_draft(session_id: str) -> GitHubProjectDraft:
    session = github_sessions.get(session_id)
    if session is None:
        raise SessionNotFoundError("Draft session not found")
    return session["draft"]


def refine_github_session(
    session_id: str, feedback: str
) -> GitHubProjectDraft:
    session = github_sessions.get(session_id)
    if session is None:
        raise SessionNotFoundError("Draft session not found")

    messages = session["messages"]
    messages.append(
        {
            "role": "user",
            "content": f"Revise the draft using this feedback: {feedback}",
        }
    )
    draft = _request_github_draft(messages)
    messages.append({"role": "assistant", "content": draft.model_dump_json()})
    session["draft"] = draft
    return draft


def refine_github_draft_without_history(feedback: str) -> GitHubProjectDraft:
    return _request_github_draft([{"role": "user", "content": feedback}])


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
