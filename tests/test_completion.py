import pytest
from types import SimpleNamespace

from models import VerificationStatus
from crud import calculate_profile_completion, get_trust_badges


def create_mock_user(
    name="Test",
    bio=None,
    interests=None,
    city=None,
    district=None,
    height=None,
    verification_status=VerificationStatus.not_verified,
):
    """Helper to create a mock user object for testing."""
    return SimpleNamespace(
        name=name,
        bio=bio,
        interests=interests,
        city=city,
        district=district,
        height=height,
        verification_status=verification_status,
    )


@pytest.mark.asyncio
async def test_calculate_profile_completion():
    """Tests the profile completion calculation logic."""

    # Test case 1: Empty profile (only has a name, as it's mandatory)
    empty_user = create_mock_user()
    completion = calculate_profile_completion(empty_user, 0)
    assert completion == 15

    # Test case 2: Full profile, not verified
    full_user_not_verified = create_mock_user(
        name="Jane",
        bio="A bio",
        interests="sport,music",
        city="Tashkent",
        height=170,
    )
    completion = calculate_profile_completion(full_user_not_verified, 1)
    # 15(name) + 25(photo) + 20(bio) + 15(interests) + 10(city) + 5(height) = 90
    assert completion == 90

    # Test case 3: Full profile, verified
    full_user_verified = create_mock_user(
        name="Jane",
        bio="A bio",
        interests="sport,music",
        city="Tashkent",
        height=170,
        verification_status=VerificationStatus.verified,
    )
    completion = calculate_profile_completion(full_user_verified, 2)
    # 15(name) + 25(photo) + 20(bio) + 15(interests) + 10(city) + 5(height) + 10(verified) = 100
    assert completion == 100

    # Test case 4: Score should not exceed 100
    completion = calculate_profile_completion(full_user_verified, 2)
    assert completion <= 100

    # Test case 5: Only district, no city
    user_with_district = create_mock_user(district="Yunusobod")
    completion = calculate_profile_completion(user_with_district, 0)
    # 15(name) + 10(district) = 25
    assert completion == 25

    # Test case 6: Truly empty profile (no name)
    truly_empty_user = create_mock_user(name=None)
    completion = calculate_profile_completion(truly_empty_user, 0)
    assert completion == 0


@pytest.mark.asyncio
async def test_get_trust_badges():
    """Tests the trust badge generation logic."""
    # Basic user
    user1 = create_mock_user()
    badges1 = get_trust_badges(user1, 0, 15, "uz")
    assert badges1 == ["✅ Telegram"]

    # User with photo
    user2 = create_mock_user()
    badges2 = get_trust_badges(user2, 1, 40, "uz")
    assert "✅ Telegram" in badges2
    assert "📸 Foto mavjud" in badges2

    # Verified user
    user3 = create_mock_user(verification_status=VerificationStatus.verified)
    badges3 = get_trust_badges(user3, 1, 50, "uz")
    assert "🛡️ Tasdiqlangan" in badges3

    # User with high completion
    user4 = create_mock_user()
    badges4 = get_trust_badges(user4, 1, 85, "uz")
    assert "⭐ To‘liq profil" in badges4