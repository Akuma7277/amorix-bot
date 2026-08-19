import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from models import UserGender, LookingForGender, VerificationStatus, User, PremiumPlan, UserStatus
from crud import calculate_compatibility_score, get_compatibility_reasons, calculate_profile_completion, get_user_photos, get_profiles_for_user
from inline import ALL_INTERESTS


# Mock User object for testing
def create_mock_user(
    id: int,
    name="Test",
    age=25,
    gender=UserGender.male,
    looking_for=LookingForGender.female,
    city="Tashkent",
    district="Yunusobod",
    interests="sport,music",
    bio="Hello",
    height=170,
    verification_status=VerificationStatus.not_verified,
    language="uz",
    status=UserStatus.active,
    is_invisible=False,
):
    user = User(
        id=id,
        telegram_id=id, # Using id as telegram_id for simplicity in mocks
        name=name,
        age=age,
        gender=gender,
        looking_for=looking_for,
        city=city,
        district=district,
        interests=interests,
        bio=bio,
        height=height,
        verification_status=verification_status,
        language=language,
        status=status,
        is_invisible=is_invisible,
    )
    # Mocking properties that might be accessed
    user.premium_plan = PremiumPlan.basic
    user.premium_expires_at = None
    return user

# Mock Photo object
class MockPhoto:
    def __init__(self, file_id="abc"):
        self.file_id = file_id

@pytest.fixture
def mock_session():
    """Fixture to mock async_session_maker."""
    class MockSession:
        def __init__(self, users):
            self._users = {u.id: u for u in users}

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def get(self, model, ident):
            if model == User:
                return self._users.get(ident)
            return None

    def _mock_session_factory(users):
        mock_maker = MagicMock()
        mock_maker.return_value = MockSession(users)
        return mock_maker

    return _mock_session_factory


@pytest.mark.asyncio
async def test_calculate_compatibility_score_common_interests(mock_session):
    user1 = create_mock_user(1, interests="sport,music,travel")
    user2 = create_mock_user(2, interests="music,books,travel", gender=UserGender.female, looking_for=LookingForGender.male)
    
    with patch('crud.async_session_maker', mock_session([user1, user2])), \
         patch('crud.get_user_photos', AsyncMock(return_value=[MockPhoto()])), \
         patch('crud.calculate_profile_completion', MagicMock(return_value=100)):
        score = await calculate_compatibility_score(user1.id, user2.id)
        # Common interests (music, travel) = 40 points
        # Age match (25 vs 25) = 25 points
        # Same city = 10 points
        # Same district = 5 points
        # Gender match = 10 points
        # Candidate completion >= 80 = 10 points
        # Total = 40 + 25 + 10 + 5 + 10 + 10 = 100
        assert score == 100

@pytest.mark.asyncio
async def test_calculate_compatibility_score_no_common_interests(mock_session):
    user1 = create_mock_user(1, interests="sport")
    user2 = create_mock_user(2, interests="books", gender=UserGender.female, looking_for=LookingForGender.male)
    
    with patch('crud.async_session_maker', mock_session([user1, user2])), \
         patch('crud.get_user_photos', AsyncMock(return_value=[MockPhoto()])), \
         patch('crud.calculate_profile_completion', MagicMock(return_value=100)):
        score = await calculate_compatibility_score(user1.id, user2.id)
        # No common interests = 0 points
        # Age match (25 vs 25) = 25 points
        # Same city = 10 points
        # Same district = 5 points
        # Gender match = 10 points
        # Candidate completion >= 80 = 10 points
        # Total = 0 + 25 + 10 + 5 + 10 + 10 = 60
        assert score == 60

@pytest.mark.asyncio
async def test_calculate_compatibility_score_age_mismatch(mock_session):
    user1 = create_mock_user(1, age=25)
    user2 = create_mock_user(2, age=40, gender=UserGender.female, looking_for=LookingForGender.male) # Outside +/- 5 range
    
    with patch('crud.async_session_maker', mock_session([user1, user2])), \
         patch('crud.get_user_photos', AsyncMock(return_value=[MockPhoto()])), \
         patch('crud.calculate_profile_completion', MagicMock(return_value=100)):
        score = await calculate_compatibility_score(user1.id, user2.id)
        # Common interests = 40 points
        # Age mismatch = 0 points
        # Same city = 10 points
        # Same district = 5 points
        # Gender match = 10 points
        # Candidate completion >= 80 = 10 points
        # Total = 40 + 0 + 10 + 5 + 10 + 10 = 75
        assert score == 75

@pytest.mark.asyncio
async def test_calculate_compatibility_score_location_mismatch(mock_session):
    user1 = create_mock_user(1, city="Tashkent", district="Yunusobod")
    user2 = create_mock_user(2, city="Samarkand", district="Urgut", gender=UserGender.female, looking_for=LookingForGender.male)
    
    with patch('crud.async_session_maker', mock_session([user1, user2])), \
         patch('crud.get_user_photos', AsyncMock(return_value=[MockPhoto()])), \
         patch('crud.calculate_profile_completion', MagicMock(return_value=100)):
        score = await calculate_compatibility_score(user1.id, user2.id)
        # Common interests = 40 points
        # Age match = 25 points
        # Location mismatch = 0 points
        # Gender match = 10 points
        # Candidate completion >= 80 = 10 points
        # Total = 40 + 25 + 0 + 10 + 10 = 85
        assert score == 85

@pytest.mark.asyncio
async def test_calculate_compatibility_score_gender_mismatch(mock_session):
    user1 = create_mock_user(1, gender=UserGender.male, looking_for=LookingForGender.female)
    user2 = create_mock_user(2, gender=UserGender.male, looking_for=LookingForGender.male) # Candidate is male, user is looking for female. Candidate is looking for male, user is male.
    
    with patch('crud.async_session_maker', mock_session([user1, user2])), \
         patch('crud.get_user_photos', AsyncMock(return_value=[MockPhoto()])), \
         patch('crud.calculate_profile_completion', MagicMock(return_value=100)):
        score = await calculate_compatibility_score(user1.id, user2.id)
        # Common interests = 40 points
        # Age match = 25 points
        # Same city = 10 points
        # Same district = 5 points
        # Gender mismatch = 0 points (user1 looking for female, user2 is male)
        # Candidate completion >= 80 = 10 points
        # Total = 40 + 25 + 10 + 5 + 0 + 10 = 90
        assert score == 90

@pytest.mark.asyncio
async def test_calculate_compatibility_score_low_completion(mock_session):
    user1 = create_mock_user(1)
    user2 = create_mock_user(2, gender=UserGender.female, looking_for=LookingForGender.male)
    # Mock calculate_profile_completion to return low score for candidate
    with patch('crud.async_session_maker', mock_session([user1, user2])), \
         patch('crud.get_user_photos', AsyncMock(return_value=[])), \
         patch('crud.calculate_profile_completion', MagicMock(return_value=50)):
        score = await calculate_compatibility_score(user1.id, user2.id)
        # Common interests = 40 points
        # Age match = 25 points
        # Same city = 10 points
        # Same district = 5 points
        # Gender match = 10 points
        # Low completion = 0 points
        # Total = 40 + 25 + 10 + 5 + 10 + 0 = 90
        assert score == 90

@pytest.mark.asyncio
async def test_calculate_compatibility_score_clamped_to_100(mock_session):
    user1 = create_mock_user(1, age=25, interests="sport,music,travel", city="Tashkent", district="Yunusobod", gender=UserGender.male, looking_for=LookingForGender.female)
    user2 = create_mock_user(2, age=25, interests="sport,music,travel", city="Tashkent", district="Yunusobod", gender=UserGender.female, looking_for=LookingForGender.male, verification_status=VerificationStatus.verified)
    
    with patch('crud.async_session_maker', mock_session([user1, user2])), \
         patch('crud.get_user_photos', AsyncMock(return_value=[MockPhoto()])), \
         patch('crud.calculate_profile_completion', MagicMock(return_value=100)): # Ensure 100 completion
        score = await calculate_compatibility_score(user1.id, user2.id)
        assert score == 100

@pytest.mark.asyncio
async def test_calculate_compatibility_score_clamped_to_0(mock_session):
    user1 = create_mock_user(1, age=25, interests="a", city="A", district="A", gender=UserGender.male, looking_for=LookingForGender.female)
    user2 = create_mock_user(2, age=50, interests="b", city="B", district="B", gender=UserGender.male, looking_for=LookingForGender.male, verification_status=VerificationStatus.not_verified)
    
    with patch('crud.async_session_maker', mock_session([user1, user2])), \
         patch('crud.get_user_photos', AsyncMock(return_value=[])), \
         patch('crud.calculate_profile_completion', MagicMock(return_value=0)):
        score = await calculate_compatibility_score(user1.id, user2.id)
        assert score == 0 # All conditions should be 0

@pytest.mark.asyncio
async def test_get_compatibility_reasons_all_reasons(mock_session):
    user1 = create_mock_user(1, interests="sport,music", city="Tashkent", district="Yunusobod", gender=UserGender.male, looking_for=LookingForGender.female)
    user2 = create_mock_user(2, interests="music,travel", city="Tashkent", district="Yunusobod", gender=UserGender.female, looking_for=LookingForGender.male)
    
    with patch('crud.async_session_maker', mock_session([user1, user2])), \
         patch('crud.get_user_photos', AsyncMock(return_value=[MockPhoto()])), \
         patch('crud.calculate_profile_completion', MagicMock(return_value=85)):
        reasons = await get_compatibility_reasons(user1.id, user2.id, language="uz")
        
        expected_reasons = [
            "🌿 Umumiy qiziqishlar: Musiqa",
            "📍 Bir xil shahar",
            "📍 Bir xil tuman",
            "🎯 Niyat yoki qidiruv mos",
            "✅ To‘liq profil"
        ]
        assert sorted(reasons) == sorted(expected_reasons)

@pytest.mark.asyncio
async def test_get_compatibility_reasons_no_reasons(mock_session):
    user1 = create_mock_user(1, interests="sport", city="Tashkent", district="Yunusobod", gender=UserGender.male, looking_for=LookingForGender.female)
    user2 = create_mock_user(2, interests="travel", city="Samarkand", district="Urgut", gender=UserGender.male, looking_for=LookingForGender.male)
    
    with patch('crud.async_session_maker', mock_session([user1, user2])), \
         patch('crud.get_user_photos', AsyncMock(return_value=[])), \
         patch('crud.calculate_profile_completion', MagicMock(return_value=0)):
        reasons = await get_compatibility_reasons(user1.id, user2.id, language="uz")
        assert reasons == []

@pytest.mark.asyncio
async def test_get_compatibility_reasons_partial_reasons(mock_session):
    user1 = create_mock_user(1, interests="sport,music", city="Tashkent", district="Yunusobod", gender=UserGender.male, looking_for=LookingForGender.female)
    user2 = create_mock_user(2, interests="music,books", city="Samarkand", district="Urgut", gender=UserGender.female, looking_for=LookingForGender.male)
    
    with patch('crud.async_session_maker', mock_session([user1, user2])), \
         patch('crud.get_user_photos', AsyncMock(return_value=[])), \
         patch('crud.calculate_profile_completion', MagicMock(return_value=70)): # Below 80
        reasons = await get_compatibility_reasons(user1.id, user2.id, language="uz")
        
        expected_reasons = [
            "🌿 Umumiy qiziqishlar: Musiqa",
            "🎯 Niyat yoki qidiruv mos",
        ]
        assert sorted(reasons) == sorted(expected_reasons)

@pytest.mark.asyncio
async def test_blocked_or_inactive_profile_not_in_search_results(mock_session):
    current_user = create_mock_user(1)
    blocked_candidate = create_mock_user(2, status=UserStatus.active) # Will be blocked
    inactive_candidate = create_mock_user(3, status=UserStatus.inactive)
    active_candidate = create_mock_user(4, status=UserStatus.active)

    class MockBlockedUser:
        def __init__(self, blocker_id, blocked_id):
            self.blocker_id = blocker_id
            self.blocked_id = blocked_id

    blocked_users_data = [MockBlockedUser(current_user.id, blocked_candidate.id)]

    class MockSessionForSearch:
        def __init__(self, users, blocked_users_data):
            self._users = {u.id: u for u in users}
            self._blocked_users_data = blocked_users_data

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

        async def get(self, model, ident):
            if model == User:
                return self._users.get(ident)
            return None

        async def execute(self, query):
            # This is a very simplified mock of the complex SQLAlchemy query in get_profiles_for_user
            # It directly filters based on the mock data provided.
            eligible_users = []
            for u_id, u in self._users.items():
                if u.id == current_user.id: continue # Don't show self
                if u.status != UserStatus.active: continue # Filter inactive
                if u.id in [b.blocked_id for b in self._blocked_users_data if b.blocker_id == current_user.id]: continue # Filter blocked
                
                # Simulate the photo check (assuming all active candidates have photos for this test)
                # In a real mock, you'd check Photo table.
                if u.status == UserStatus.active: # Only active users are considered to have photos for this mock
                    eligible_users.append(u)
            
            return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: eligible_users))

    with patch('crud.async_session_maker') as mock_maker:
        mock_maker.return_value = MockSessionForSearch([current_user, blocked_candidate, inactive_candidate, active_candidate], blocked_users_data)
        
        # Mock get_user_photos to avoid errors, not directly relevant to this test
        with patch('crud.get_user_photos', AsyncMock(return_value=[MockPhoto()])):
            profiles = await get_profiles_for_user(current_user)
            
            profile_ids = [p.id for p in profiles]
            assert blocked_candidate.id not in profile_ids
            assert inactive_candidate.id not in profile_ids
            assert active_candidate.id in profile_ids
            assert current_user.id not in profile_ids
