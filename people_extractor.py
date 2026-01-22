from dataclasses import dataclass
from typing import List, Optional
import re

@dataclass
class PersonInfo:
    name: str = ""
    expertise: str = ""
    social_media: str = ""
    email: str = ""
    company: str = ""
    degree: str = ""

# Very lightweight heuristic extraction from plain text. This is not perfect,
# but provides useful signal without requiring external dependencies.
EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
TWITTER_RE = re.compile(r"(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/([A-Za-z0-9_]{1,15})", re.I)
LINKEDIN_RE = re.compile(r"(?:https?://)?(?:[\w.-]+\.)?linkedin\.com/(?:in|pub)/([A-Za-z0-9-_%]+)", re.I)
GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9-]{1,39})", re.I)
NAME_BYLINE_RE = re.compile(r"^(?:by|author)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\b", re.I | re.M)
DEGREE_RE = re.compile(r"\b(PhD|MSc|MS|BSc|BA|MD|MBA|MPhil|DPhil)\b")
ROLE_RE = re.compile(r"\b(Professor|Researcher|Scientist|Engineer|Data Scientist|CEO|CTO|CIO|Founder|Co-?founder|Lecturer|Postdoc|Postdoctoral\s+Researcher)\b", re.I)
COMPANY_NEARBY_RE = re.compile(r"\b(?:at|@)\s+([A-Z][\w&.,'-]+(?:\s+[A-Z][\w&.,'-]+)*)")


def extract_people_info(text: str) -> List[PersonInfo]:
    people: List[PersonInfo] = []
    if not text:
        return people

    # Emails
    emails = set(m.group(0) for m in EMAIL_RE.finditer(text))

    # Socials
    handles = []
    handles += ["twitter:" + m.group(1) for m in TWITTER_RE.finditer(text)]
    handles += ["linkedin:" + m.group(1) for m in LINKEDIN_RE.finditer(text)]
    handles += ["github:" + m.group(1) for m in GITHUB_RE.finditer(text)]
    social_str = ", ".join(sorted(set(handles)))

    # Name via byline
    name_match = NAME_BYLINE_RE.search(text)
    name = name_match.group(1).strip() if name_match else ""

    # Degree
    degree_match = DEGREE_RE.search(text)
    degree = degree_match.group(1) if degree_match else ""

    # Expertise/role
    role_match = ROLE_RE.search(text)
    expertise = role_match.group(1) if role_match else ""

    # Company (look near the role or name occurrences)
    company = ""
    context_snippets: List[str] = []
    if name:
        # take a 200-char window around the name if possible
        idx = text.lower().find(name.lower())
        if idx != -1:
            start = max(0, idx - 120)
            end = min(len(text), idx + 120)
            context_snippets.append(text[start:end])
    if expertise and not context_snippets:
        idx = text.lower().find(expertise.lower())
        if idx != -1:
            start = max(0, idx - 120)
            end = min(len(text), idx + 120)
            context_snippets.append(text[start:end])

    for snip in context_snippets or [text[:300]]:
        cm = COMPANY_NEARBY_RE.search(snip)
        if cm:
            company = cm.group(1).strip()
            break

    # If we have some signal (email/social/name/role/degree/company), record a single person row.
    if name or emails or handles or expertise or degree or company:
        # choose one email if multiple
        email = next(iter(emails)) if emails else ""
        people.append(PersonInfo(
            name=name,
            expertise=expertise,
            social_media=social_str,
            email=email,
            company=company,
            degree=degree,
        ))

    return people