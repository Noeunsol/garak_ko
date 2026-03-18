from typing import List, Dict, Any

from garak.resources.runtime_common import get_target_lang, normalize_lang_code


_BRAND_MAP = {
    "amazon": "Amazon",
    "aws": "AWS",
    "s3": "S3",
    "sns": "SNS",
    "mws": "MWS",
    "api": "API",
    "id": "ID",
    "url": "URL",
    "uri": "URI",
    "oauth": "OAuth",
    "fcm": "FCM",
    "github": "GitHub",
    "linkedin": "LinkedIn",
    "mailchimp": "Mailchimp",
    "mailgun": "Mailgun",
    "mongodb": "MongoDB",
    "paypal": "PayPal",
    "pypi": "PyPI",
    "nuget": "NuGet",
    "sendgrid": "SendGrid",
    "cloudinary": "Cloudinary",
    "dynatrace": "Dynatrace",
    "facebook": "Facebook",
    "google": "Google",
    "microsoft": "Microsoft",
    "teams": "Teams",
    "riot": "Riot",
    "slack": "Slack",
    "twilio": "Twilio",
    "discord": "Discord",
    "shopify": "Shopify",
    "stripe": "Stripe",
    "twitter": "Twitter",
    "square": "Square",
    "stackhawk": "StackHawk",
    "picatic": "Picatic",
    "zapier": "Zapier",
    "zoho": "Zoho",
    "bitly": "Bitly",
    "heroku": "Heroku",
    "notion": "Notion",
    "serpapi": "SerpAPI",
}

_TYPE_MAP = {
    "access": "액세스",
    "secret": "시크릿",
    "token": "토큰",
    "webhook": "웹훅",
    "client": "클라이언트",
    "refresh": "리프레시",
    "private": "프라이빗",
    "personal": "개인",
    "application": "애플리케이션",
    "admin": "관리자",
    "insights": "인사이트",
    "location": "위치",
    "connection": "연결",
    "string": "문자열",
    "server": "서버",
    "shared": "공유",
    "custom": "커스텀",
    "standard": "표준",
    "restricted": "제한",
    "developer": "개발자",
    "upload": "업로드",
    "integration": "통합",
    "calendar": "캘린더",
    "topic": "토픽",
    "credentials": "자격 증명",
    "auth": "인증",
    "key": "키",
}

def _title_case(key: str) -> str:
    return key.replace("_", " ").title()


def _ko_label_from_key(key: str) -> str:
    tokens = key.split("_")
    words = []
    for token in tokens:
        if token in _TYPE_MAP:
            words.append(_TYPE_MAP[token])
        elif token in _BRAND_MAP:
            words.append(_BRAND_MAP[token])
        else:
            words.append(token.title())
    return " ".join(words)


def extract_key_types(
    regex_dict_list: List[Dict[str, Any]], target_lang: str | None = None
) -> List[str]:
    """Return service labels from regex keys, localized for the requested language."""
    all_keys = [key for dict in regex_dict_list for key in dict]
    resolved_lang = normalize_lang_code(
        target_lang if target_lang is not None else get_target_lang()
    )
    if resolved_lang == "ko":
        return [_ko_label_from_key(key) for key in all_keys]
    return [_title_case(key) for key in all_keys]
