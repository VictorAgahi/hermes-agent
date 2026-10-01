from common.v1 import event_pb2 as _event_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ChallengeType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CHALLENGE_TYPE_UNSPECIFIED: _ClassVar[ChallengeType]
    CHALLENGE_TYPE_SMS_OTP: _ClassVar[ChallengeType]
    CHALLENGE_TYPE_APP_TOTP: _ClassVar[ChallengeType]
    CHALLENGE_TYPE_CLOUDFLARE_TURNSTILE: _ClassVar[ChallengeType]
    CHALLENGE_TYPE_IMAGE_CAPTCHA: _ClassVar[ChallengeType]
CHALLENGE_TYPE_UNSPECIFIED: ChallengeType
CHALLENGE_TYPE_SMS_OTP: ChallengeType
CHALLENGE_TYPE_APP_TOTP: ChallengeType
CHALLENGE_TYPE_CLOUDFLARE_TURNSTILE: ChallengeType
CHALLENGE_TYPE_IMAGE_CAPTCHA: ChallengeType

class ChallengeDetected(_message.Message):
    __slots__ = ("header", "challenge_id", "trace_id", "type", "target_site_name", "screenshot_path", "timeout_seconds", "short_session_token")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    CHALLENGE_ID_FIELD_NUMBER: _ClassVar[int]
    TRACE_ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    TARGET_SITE_NAME_FIELD_NUMBER: _ClassVar[int]
    SCREENSHOT_PATH_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_SECONDS_FIELD_NUMBER: _ClassVar[int]
    SHORT_SESSION_TOKEN_FIELD_NUMBER: _ClassVar[int]
    header: _event_pb2.EventHeader
    challenge_id: str
    trace_id: str
    type: ChallengeType
    target_site_name: str
    screenshot_path: str
    timeout_seconds: int
    short_session_token: str
    def __init__(self, header: _Optional[_Union[_event_pb2.EventHeader, _Mapping]] = ..., challenge_id: _Optional[str] = ..., trace_id: _Optional[str] = ..., type: _Optional[_Union[ChallengeType, str]] = ..., target_site_name: _Optional[str] = ..., screenshot_path: _Optional[str] = ..., timeout_seconds: _Optional[int] = ..., short_session_token: _Optional[str] = ...) -> None: ...

class InputInjection(_message.Message):
    __slots__ = ("header", "challenge_id", "text_value", "target_input_selector", "submit_form_after")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    CHALLENGE_ID_FIELD_NUMBER: _ClassVar[int]
    TEXT_VALUE_FIELD_NUMBER: _ClassVar[int]
    TARGET_INPUT_SELECTOR_FIELD_NUMBER: _ClassVar[int]
    SUBMIT_FORM_AFTER_FIELD_NUMBER: _ClassVar[int]
    header: _event_pb2.EventHeader
    challenge_id: str
    text_value: str
    target_input_selector: str
    submit_form_after: bool
    def __init__(self, header: _Optional[_Union[_event_pb2.EventHeader, _Mapping]] = ..., challenge_id: _Optional[str] = ..., text_value: _Optional[str] = ..., target_input_selector: _Optional[str] = ..., submit_form_after: _Optional[bool] = ...) -> None: ...

class SessionSuspended(_message.Message):
    __slots__ = ("header", "session_id", "target_url", "reason", "freed_memory_bytes", "resume_token")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    TARGET_URL_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    FREED_MEMORY_BYTES_FIELD_NUMBER: _ClassVar[int]
    RESUME_TOKEN_FIELD_NUMBER: _ClassVar[int]
    header: _event_pb2.EventHeader
    session_id: str
    target_url: str
    reason: str
    freed_memory_bytes: int
    resume_token: str
    def __init__(self, header: _Optional[_Union[_event_pb2.EventHeader, _Mapping]] = ..., session_id: _Optional[str] = ..., target_url: _Optional[str] = ..., reason: _Optional[str] = ..., freed_memory_bytes: _Optional[int] = ..., resume_token: _Optional[str] = ...) -> None: ...

class SessionResumed(_message.Message):
    __slots__ = ("header", "resume_token", "target_url", "restore_cookies")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    RESUME_TOKEN_FIELD_NUMBER: _ClassVar[int]
    TARGET_URL_FIELD_NUMBER: _ClassVar[int]
    RESTORE_COOKIES_FIELD_NUMBER: _ClassVar[int]
    header: _event_pb2.EventHeader
    resume_token: str
    target_url: str
    restore_cookies: bool
    def __init__(self, header: _Optional[_Union[_event_pb2.EventHeader, _Mapping]] = ..., resume_token: _Optional[str] = ..., target_url: _Optional[str] = ..., restore_cookies: _Optional[bool] = ...) -> None: ...

class BrowserNavigateRequest(_message.Message):
    __slots__ = ("header", "url", "action", "wait_selector", "timeout_seconds", "session_cookies")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    WAIT_SELECTOR_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_SECONDS_FIELD_NUMBER: _ClassVar[int]
    SESSION_COOKIES_FIELD_NUMBER: _ClassVar[int]
    header: _event_pb2.EventHeader
    url: str
    action: str
    wait_selector: str
    timeout_seconds: int
    session_cookies: str
    def __init__(self, header: _Optional[_Union[_event_pb2.EventHeader, _Mapping]] = ..., url: _Optional[str] = ..., action: _Optional[str] = ..., wait_selector: _Optional[str] = ..., timeout_seconds: _Optional[int] = ..., session_cookies: _Optional[str] = ...) -> None: ...

class BrowserNavigateResponse(_message.Message):
    __slots__ = ("header", "status", "error_message", "screenshot_path", "downloaded_file_path", "cookies_json")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    SCREENSHOT_PATH_FIELD_NUMBER: _ClassVar[int]
    DOWNLOADED_FILE_PATH_FIELD_NUMBER: _ClassVar[int]
    COOKIES_JSON_FIELD_NUMBER: _ClassVar[int]
    header: _event_pb2.EventHeader
    status: str
    error_message: str
    screenshot_path: str
    downloaded_file_path: str
    cookies_json: str
    def __init__(self, header: _Optional[_Union[_event_pb2.EventHeader, _Mapping]] = ..., status: _Optional[str] = ..., error_message: _Optional[str] = ..., screenshot_path: _Optional[str] = ..., downloaded_file_path: _Optional[str] = ..., cookies_json: _Optional[str] = ...) -> None: ...
