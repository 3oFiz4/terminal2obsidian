# context/args_parsing.py

from pathlib import Path
from typing import Tuple
import re
import typer
from rich.text import Text
from rich.console import Console

from services.error_logger import Panic
from services.profile_manager import ProfileManager
from models.profile import ProfileDTO


console = Console()

class ArgsParser:
    _FORBIDDEN_FS_CHARS: tuple[str, ...] = ("<", ">", '"', "|", "?", "*")

    def __init__(self) -> None:
        self.app = typer.Typer(
            name="notes",
            help="CLI entrypoint for note operations.",
            no_args_is_help=True,
            add_completion=False,
        )
        self._register_commands()

    def _register_commands(self) -> None:
        """Registers all available commands to the Typer app."""
        self.app.command(name="create_note")(self.create_note)

    def _validate_name(self, name: str) -> str:
        cleaned_name = name.strip() # remove leading/trailing whitespace

        if not cleaned_name:
            # 1. Empty name check
            Panic(
                ValueError,
                "The profile name cannot be empty or whitespace.",
                solutions=[
                    "Provide a valid profile name as the first argument",
                    'Example: --profileDTO "Financial" "D:\\note"',
                ],
                note="CLI profileDTO empty name validation triggered"
            )
            return None

        for forbidden_char in self._FORBIDDEN_FS_CHARS:
            if forbidden_char in cleaned_name:
                # 2. FileSystem name violation check
                Panic(
                    ValueError,
                    f"Target terminal string contains invalid file-system tracking character: '{forbidden_char}'",
                    solutions=[
                        "Ensure windows paths do not include trailing pipe symbols or unclosed structures.",
                        "Wrap paths containing whitespaces completely inside valid string containers."
                    ],
                    note="CLI FileSystem naming violation pattern intercepted"
                )
                return None

        return cleaned_name

    def _validate_path(self, path_str: str) -> Path:
        cleaned_path = path_str.strip()

        if not cleaned_path:
            # 1. Empty path check
            Panic(
                ValueError,
                "The profile path cannot be empty or whitespace.",
                solutions=[
                    "Provide a valid directory path as the second argument",
                    'Example: --profileDTO "MyProfile" "D:\\note\\Financial"',
                ],
                note="CLI profileDTO empty path validation triggered"
            )
            return None

        for forbidden_char in self._FORBIDDEN_FS_CHARS:
            if forbidden_char in cleaned_path:
                # 2. FileSystem path violation check
                Panic(
                    ValueError,
                    f"Target terminal string contains invalid file-system tracking character: '{forbidden_char}'",
                    solutions=[
                        "Ensure windows paths do not include trailing pipe symbols or unclosed structures.",
                        "Wrap paths containing whitespaces completely inside valid string containers."
                    ],
                    note="CLI FileSystem naming violation pattern intercepted"
                )
                return None

        if ":" in cleaned_path and not re.match(r"^[A-Za-z]:[\\/]", cleaned_path):
            # 3. Drive prefix check
            Panic(
                ValueError,
                "The provided path contains ':' in an invalid position.",
                solutions=[
                    r"Use a valid Windows drive prefix like C:\note\Financial",
                    "Remove ':' characters that are not part of the drive prefix",
                ],
                note="CLI profileDTO drive-prefix validation failed"
            )
            return None

        return Path(cleaned_path).expanduser()

    def create_note(
        self,
        profileDTO: Tuple[str, str] = typer.Option(
            ...,
            "--create-profile",
            metavar="NAME PATH",
            help="Profile definition: <name> <path>",
            show_default=False,
        ),
        is_default: bool = typer.Option(
            True,
            "--default/--no-default",
            help="Set this profile as default (default: True)",
        ),
    ) -> None:
        """Creates a note using the specified profile configuration."""
        name_raw, path_raw = profileDTO

        validated_name = self._validate_name(name_raw)
        validated_path = self._validate_path(path_raw)
        if (validated_name and validated_path):
            try:
                profile = ProfileDTO(
                    path=validated_path,
                    isDefault=is_default,
                    name=validated_name,
                )
                response = Text()
                response.append(f"[create_note] Profile declared:\n", style="green")
                response.append(f"  Name:      {profile.name}\n", style="green")
                response.append(f"  Path:      {profile.path}\n", style="green")
                response.append(f"  isDefault: {profile.isDefault}\n", style="green")
                console.print(response)

                profile_mngr = ProfileManager()
                profile_mngr.add_profile(profile)
                print(profile_mngr)
            except:
                # The reason try-except exist here is that, even if $name and $path is not validated, this adds an error, even though error_logger already explain the error.. so useless.
                pass

    def run(self) -> None:
        self.app()


cli = ArgsParser()
app = cli.app
