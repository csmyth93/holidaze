import re
import zipfile
from datetime import datetime
from pathlib import Path

from .models import Message


# WhatsApp message format: [DD/MM/YYYY, HH:MM:SS] Sender: Message
MESSAGE_PATTERN = re.compile(
    r"^\[(\d{2}/\d{2}/\d{4}), (\d{2}:\d{2}:\d{2})\] ([^:]+): (.+)$",
    re.DOTALL
)

# System message indicators - these are not real user messages
SYSTEM_INDICATORS = [
    "Messages and calls are end-to-end encrypted",
    "created group",
    "added you",
    "changed the group",
    "pinned a message",
    "image omitted",
    "video omitted",
    "document omitted",
    "GIF omitted",
    "Voice call",
    "Waiting for this message",
    "This message was deleted",
    "POLL:",
    "sticker omitted",
    "audio omitted",
]


class WhatsAppParser:
    """Parse WhatsApp chat export into structured messages."""

    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)

    def parse(self) -> list[Message]:
        """Extract all messages from the chat file or zip."""
        content = self._read_content()
        raw_messages = self._split_messages(content)
        messages = []

        for raw in raw_messages:
            msg = self._parse_message(raw)
            if msg:
                messages.append(msg)

        return messages

    def _read_content(self) -> str:
        """Read content from zip or text file."""
        if self.file_path.suffix == ".zip":
            with zipfile.ZipFile(self.file_path, "r") as zf:
                # Find the chat file inside the zip
                for name in zf.namelist():
                    if name.endswith(".txt"):
                        return zf.read(name).decode("utf-8")
                raise ValueError("No .txt file found in zip archive")
        else:
            return self.file_path.read_text(encoding="utf-8")

    def _split_messages(self, content: str) -> list[str]:
        """Split content into individual messages, handling multiline."""
        lines = content.split("\n")
        messages = []
        current_message = []

        for line in lines:
            # Check if this line starts a new message
            if re.match(r"^\[\d{2}/\d{2}/\d{4}, \d{2}:\d{2}:\d{2}\]", line):
                # Save previous message if exists
                if current_message:
                    messages.append("\n".join(current_message))
                current_message = [line]
            else:
                # Continuation of previous message
                if current_message:
                    current_message.append(line)

        # Don't forget the last message
        if current_message:
            messages.append("\n".join(current_message))

        return messages

    def _parse_message(self, raw: str) -> Message | None:
        """Parse a single raw message string into a Message object."""
        # Handle the special character that WhatsApp uses
        raw = raw.replace("\u200e", "")

        match = MESSAGE_PATTERN.match(raw)
        if not match:
            return None

        date_str, time_str, sender, content = match.groups()

        # Parse datetime
        try:
            timestamp = datetime.strptime(
                f"{date_str} {time_str}", "%d/%m/%Y %H:%M:%S"
            )
        except ValueError:
            return None

        # Check if this is a system message
        is_system = any(indicator in content for indicator in SYSTEM_INDICATORS)

        return Message(
            timestamp=timestamp,
            sender=sender.strip(),
            content=content.strip(),
            is_system=is_system,
        )

    def get_participants(self, messages: list[Message]) -> list[str]:
        """Extract unique participants from messages, excluding system senders."""
        system_senders = {"Birkencrocs Crew"}  # Group name used for system messages
        participants = set()

        for msg in messages:
            if not msg.is_system and msg.sender not in system_senders:
                participants.add(msg.sender)

        return sorted(participants)
