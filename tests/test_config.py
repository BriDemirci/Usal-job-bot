import json
from pathlib import Path

def test_config_files_exist_and_valid():
    config_dir = Path(__file__).parent.parent / "config"
    profile_path = config_dir / "profile.json"
    criteria_path = config_dir / "criteria.json"

    assert profile_path.exists(), "profile.json debe existir"
    assert criteria_path.exists(), "criteria.json debe existir"

    with open(profile_path, "r", encoding="utf-8") as f:
        profile = json.load(f)
        assert "full_name" in profile
        assert "career" in profile
        assert "skills" in profile
        assert isinstance(profile["skills"], list)

    with open(criteria_path, "r", encoding="utf-8") as f:
        criteria = json.load(f)
        assert "min_fit_score" in criteria
        assert 0 <= criteria["min_fit_score"] <= 100
        assert "target_roles" in criteria
