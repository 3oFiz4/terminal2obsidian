from dataclasses import dataclass
from pathlib import Path
from services.error_logger import Panic

@dataclass(frozen=True)
class ProfileDTO:
    path: Path
    isDefault: bool = True
    name: str = ""
    #TODO: Apply debugger here
    def __post_init__(self):
        """Runs right after initialization to enforce data integrity and safe handling."""
        
        # 1. Type Validation for 'path'
        # below means 
        if not isinstance(self.path, (str, Path)):
            Panic(
                TypeError,
                f"Invalid path type: {type(self.path).__name__}",
                solutions=[
                    "Pass a raw string path, e.g., r'D:\\note\\Financial'",
                    "Pass a valid pathlib.Path object",
                ],
                note="ProfileDTO path assignment failed during initialization"
            )
        
        # 2. Empty path check
        if not str(self.path).strip():
            Panic(
                ValueError,
                "The profile path cannot be empty or just whitespace.",
                solutions=[
                    "Provide a valid directory or file path text sequence",
                    "Check if your configurations configuration variable is empty",
                ],
                note="ProfileDTO empty path assignment validation triggered"
            )

        # Normalize and set the clean path string/object
        normalized_path = Path(str(self.path).strip()).resolve()
        object.__setattr__(self, "path", normalized_path)

        # 3. Type Validation for 'isDefault'
        if not isinstance(self.isDefault, bool):
            object.__setattr__(self, "isDefault", bool(self.isDefault))

        # 4. Type Validation for 'name'
        if not isinstance(self.name, str):
            Panic(
                TypeError,
                f"Invalid name type: {type(self.name).__name__}",
                solutions=[
                    "Ensure the name parameter is wrapped in quotation marks",
                    "Pass an empty string \"\" if a specific name is not required",
                ],
                note="ProfileDTO name validation failed"
            )
        
        object.__setattr__(self, "name", self.name.strip())
