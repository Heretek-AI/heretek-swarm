"""
Character System for ElizaOS-style agents.

This module provides the character definition and loading system,
inspired by the elizaOS character format.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import structlog

logger = structlog.get_logger("CharacterSystem")


@dataclass
class CharacterStyle:
    """Defines the character's communication style."""

    all: list[str] = field(default_factory=list)
    chat: list[str] = field(default_factory=list)
    speak: list[str] = field(default_factory=list)


@dataclass
class Character:
    """
    Character definition for an agent.

    Contains all the configuration needed to define an agent's
    personality, knowledge, and behavior patterns.
    """

    name: str
    role: str
    bio: str
    lore: str = ""
    knowledge: list[str] = field(default_factory=list)
    message_examples: list[list[list[str]]] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    style: CharacterStyle = field(default_factory=CharacterStyle)
    adjectives: list[str] = field(default_factory=list)
    goals: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Character":
        """
        Create a Character from a dictionary.

        Args:
            data: Character definition dictionary

        Returns:
            Character instance
        """
        style_data = data.get("style", {})
        style = CharacterStyle(
            all=style_data.get("all", []),
            chat=style_data.get("chat", []),
            speak=style_data.get("speak", []),
        )

        return cls(
            name=data.get("name", "Unknown"),
            role=data.get("role", "agent"),
            bio=data.get("bio", ""),
            lore=data.get("lore", ""),
            knowledge=data.get("knowledge", []),
            message_examples=data.get("messageExamples", []),
            topics=data.get("topics", []),
            style=style,
            adjectives=data.get("adjectives", []),
            goals=data.get("goals", []),
            constraints=data.get("constraints", []),
        )

    @classmethod
    def from_json(cls, json_path: Path) -> "Character":
        """
        Load a character from a JSON file.

        Args:
            json_path: Path to the character JSON file

        Returns:
            Character instance
        """
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        logger.info(f"Loaded character: {data.get('name', 'Unknown')}")
        return cls.from_dict(data)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert character to dictionary.

        Returns:
            Character definition dictionary
        """
        return {
            "name": self.name,
            "role": self.role,
            "bio": self.bio,
            "lore": self.lore,
            "knowledge": self.knowledge,
            "messageExamples": self.message_examples,
            "topics": self.topics,
            "style": {
                "all": self.style.all,
                "chat": self.style.chat,
                "speak": self.style.speak,
            },
            "adjectives": self.adjectives,
            "goals": self.goals,
            "constraints": self.constraints,
        }

    def generate_system_prompt(self) -> str:
        """
        Generate a system prompt from the character definition.

        Returns:
            Formatted system prompt
        """
        parts = []

        # Basic identity
        parts.append(f"You are {self.name}, a {self.role}.")
        parts.append(f"Bio: {self.bio}")

        # Lore and background
        if self.lore:
            parts.append(f"Background: {self.lore}")

        # Knowledge areas
        if self.knowledge:
            parts.append(f"Knowledge domains: {', '.join(self.knowledge)}")

        # Topics of expertise
        if self.topics:
            parts.append(f"Topics: {', '.join(self.topics)}")

        # Communication style
        if self.style.all:
            parts.append(f"Communication style: {', '.join(self.style.all)}")

        # Adjectives that describe the character
        if self.adjectives:
            parts.append(f"Your qualities: {', '.join(self.adjectives)}")

        # Goals
        if self.goals:
            parts.append(f"Your goals: {'; '.join(self.goals)}")

        # Constraints
        if self.constraints:
            parts.append(f"Constraints: {'; '.join(self.constraints)}")

        return "\n\n".join(parts)

    def validate(self) -> list[str]:
        """
        Validate the character definition.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not self.name:
            errors.append("Character name is required")

        if not self.role:
            errors.append("Character role is required")

        if not self.bio:
            errors.append("Character bio is required")

        return errors


class CharacterRegistry:
    """
    Registry for managing character definitions.

    Provides loading, caching, and lookup capabilities for
    character definitions.
    """

    def __init__(self, characters_dir: Optional[Path] = None) -> None:
        """
        Initialize the character registry.

        Args:
            characters_dir: Directory containing character JSON files
        """
        self.characters_dir = characters_dir or Path(__file__).parent / "characters"
        self._characters: dict[str, Character] = {}
        self._load_all()

    def _load_all(self) -> None:
        """Load all character definitions from the characters directory."""
        if not self.characters_dir.exists():
            logger.warning(f"Characters directory not found: {self.characters_dir}")
            return

        for json_file in self.characters_dir.glob("*.json"):
            try:
                character = Character.from_json(json_file)
                self._characters[character.name.lower()] = character
                logger.debug(f"Loaded character: {character.name}")
            except Exception as e:
                logger.error(f"Failed to load character {json_file}: {e}")

    def get(self, name: str) -> Optional[Character]:
        """
        Get a character by name.

        Args:
            name: Character name (case-insensitive)

        Returns:
            Character instance or None if not found
        """
        return self._characters.get(name.lower())

    def get_by_role(self, role: str) -> list[Character]:
        """
        Get all characters with a specific role.

        Args:
            role: Role to filter by

        Returns:
            List of matching characters
        """
        return [c for c in self._characters.values() if c.role == role]

    def list_characters(self) -> list[str]:
        """
        List all available character names.

        Returns:
            List of character names
        """
        return list(self._characters.keys())

    def register(self, character: Character) -> None:
        """
        Register a new character.

        Args:
            character: Character to register
        """
        self._characters[character.name.lower()] = character
        logger.info(f"Registered character: {character.name}")

    def unregister(self, name: str) -> bool:
        """
        Unregister a character.

        Args:
            name: Character name

        Returns:
            True if character was removed, False if not found
        """
        key = name.lower()
        if key in self._characters:
            del self._characters[key]
            logger.info(f"Unregistered character: {name}")
            return True
        return False


# Global registry instance
_default_registry: Optional[CharacterRegistry] = None


def get_character_registry() -> CharacterRegistry:
    """
    Get the global character registry.

    Returns:
        CharacterRegistry instance
    """
    global _default_registry
    if _default_registry is None:
        _default_registry = CharacterRegistry()
    return _default_registry


def load_character(name: str) -> Optional[Character]:
    """
    Load a character by name from the global registry.

    Args:
        name: Character name

    Returns:
        Character instance or None if not found
    """
    return get_character_registry().get(name)


def list_characters() -> list[str]:
    """
    List all available character names.

    Returns:
        List of character names
    """
    return get_character_registry().list_characters()