from pathlib import Path
from services.error_logger import Panic
from services.debug_logger import Debug
from models.profile import ProfileDTO
Debug.enabled = True # for developer
class ProfileManager:
    @Debug.observe(tag="PROFILE_INIT")
    def __init__(self):
        self._profiles: set[ProfileDTO] = set()

    @Debug.observe(tag="PROFILE_ADD")
    def add_profile(self, profile: ProfileDTO) -> None:
        """Safely accepts and stores a ProfileDTO, checking for duplicate contexts."""
        if not isinstance(profile, ProfileDTO):
            Panic(
                TypeError,
                f"ProfileManager only accepts ProfileDTO, got {type(profile).__name__}",
                solutions=[
                    "Instantiate a ProfileDTO object before passing it to add_profile()",
                    "Use ProfileManager.create_profile() to build and manage it inline automatically",
                ],
                note="Strict runtime structure typing check failed inside add_profile()"
            )
        
        # 1. Check if exact duplicate object structure already exists inside our tracked set
        if profile in self._profiles:
            Panic(
                ValueError,
                f"Profile with path '{profile.path}' and name '{profile.name}' is already registered.",
                solutions=[
                    "Verify if you accidentally executed add_profile() on the same item twice",
                    "Change the name or path properties to register a distinct profile structure",
                ],
                note="Set duplicate mitigation caught an identical profile entry registry sequence"
            )

        # 2. Check if a profile with this exact PATH already exists under a separate configuration wrapper
        if any(p.path == profile.path for p in self._profiles):
            Panic(
                ValueError,
                f"A profile setup pointing to target directory '{profile.path}' already exists.",
                solutions=[
                    "Use the existing profile object registered under this path instead",
                    "If updates are required, clear or drop the old profile records first",
                ],
                note="Path exclusivity collision intercepted"
            )
        
        # 3. Duplicate Default Mitigation
        # TODO: Provide an option whether user meant to re-position the $default to another profile
        if profile.isDefault and any(p.isDefault for p in self._profiles):
            Panic(
                ValueError,
                f"Cannot add default profile '{profile.name}'. A master default profile configuration tracker already exists.",
                solutions=[
                    "Pass isDefault=False when defining secondary fallback structural profiles",
                    "Implement a sequence to loop through current profiles and set their isDefault properties to False first",
                ],
                note="Single default configuration environment rule violated"
            )
            
        self._profiles.add(profile)

    @Debug.observe(tag="PROFILE_CREATE")
    def create_profile(self, path: Path, isDefault: bool = True, name: str = "") -> ProfileDTO:
        """Wraps profile creation. Panic will catch inner anomalies automatically."""
        dto = ProfileDTO(path=path, isDefault=isDefault, name=name)
        self.add_profile(dto)
        return dto

    @Debug.observe(tag="PROFILE___STR__")
    def __str__(self) -> str:
        return str(self._profiles)

    @Debug.observe(tag="PROFILE___REPR__")
    def __repr__(self) -> str:
        return f"ProfileManager({self._profiles})"
