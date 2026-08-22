import pytest
import pytest_asyncio
import aiohttp
from aiohttp.test_utils import TestClient, TestServer
from webapp.api import create_webapp_app
from models import Base, User, UserStatus
import engine as engine_module
from crud import create_user_profile, verify_user, get_user_by_telegram_id
from i18n import t

@pytest_asyncio.fixture
async def client():
    async with engine_module.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    app = create_webapp_app()
    client = TestClient(TestServer(app))
    await client.start_server()
    yield client
    await client.close()

class TestAmorixEnterpriseSuite:

    @pytest.mark.asyncio
    async def test_health_and_system(self, client):
        resp = await client.get("/health")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "ok"

        ready_resp = await client.get("/health/ready")
        assert ready_resp.status == 200
        ready_data = await ready_resp.json()
        assert ready_data["status"] == "ready"

    @pytest.mark.asyncio
    async def test_i18n_multilanguage_system(self):
        # 1. Test Uzbek translation
        assert "Muloqot tilini tanlang" in t("choose_language", "uz")
        assert "Ismingizni kiriting" in t("ask_name", "uz")
        assert "Foydalanish Qoidalari" in t("terms_title", "uz")
        
        # 2. Test Russian translation
        assert "Выберите язык" in t("choose_language", "ru")
        assert "Введите ваше имя" in t("ask_name", "ru")
        assert "Правила использования" in t("terms_title", "ru")

        # 3. Test English translation
        assert "Choose your language" in t("choose_language", "en")
        assert "Enter your name" in t("ask_name", "en")
        assert "Terms of Service" in t("terms_title", "en")

    @pytest.mark.asyncio
    async def test_instant_active_registration(self):
        # Create user via selection-based registration flow
        user_data = {
            "name": "Shahzod",
            "age": 23,
            "gender": "MALE",
            "looking_for": "FEMALE",
            "height": 178,
            "relationship_intent": "SERIOUS_RELATIONSHIP",
            "city": "Toshkent shahri",
            "district": "Yunusobod",
            "interests": ["gaming", "fitness"],
            "bio": "Dasturchi va kitobxon",
            "language": "uz",
            "photos": ["file_id_mock_123"]
        }
        
        user = await create_user_profile(telegram_id=99001122, user_data=user_data)
        assert user is not None
        assert user.name == "Shahzod"
        assert user.age == 23
        assert user.status.value in ["ACTIVE", "APPROVED", "active", "approved"]
        assert user.is_verified is False # Initially not verified

        # User is immediately active and found in db
        db_user = await get_user_by_telegram_id(99001122)
        assert db_user.status.value in ["ACTIVE", "APPROVED", "active", "approved"]

    @pytest.mark.asyncio
    async def test_admin_post_moderation_verification_badge(self):
        user_data = {
            "name": "Madina",
            "age": 21,
            "gender": "FEMALE",
            "looking_for": "MALE",
            "city": "Samarqand",
            "language": "ru",
            "photos": ["file_photo_madina"]
        }
        user = await create_user_profile(telegram_id=88112233, user_data=user_data)
        assert user.is_verified is False

        # Admin approves verification badge
        verified_user = await verify_user(user_id=user.id, admin_telegram_id=7992878834, is_verified=True)
        assert verified_user.is_verified is True

        # Admin un-verifies
        unverified_user = await verify_user(user_id=user.id, admin_telegram_id=7992878834, is_verified=False)
        assert unverified_user.is_verified is False

    @pytest.mark.asyncio
    async def test_webapp_receipt_payment_checkout_flow(self, client):
        await client.get("/api/session?initData=mock_user_2001")

        order_resp = await client.post("/api/payment/submit?initData=mock_user_2001", json={
            "plan_tier": "VIP",
            "period": "yearly",
            "amount": 710000.0,
            "receipt_photo": "data:image/jpeg;base64,mock_receipt_image_data"
        })
        assert order_resp.status == 200
        order_id = (await order_resp.json())["order_id"]

        adm_payments_resp = await client.get("/api/admin/payments?initData=mock_admin")
        assert adm_payments_resp.status == 200
        adm_data = await adm_payments_resp.json()
        assert len(adm_data["orders"]) >= 1

        approve_resp = await client.post("/api/admin/payment/approve?initData=mock_admin", json={"order_id": order_id})
        assert approve_resp.status == 200

        user_sess = await (await client.get("/api/session?initData=mock_user_2001")).json()
        assert user_sess["user"]["plan_tier"] == "VIP"
        assert user_sess["user"]["is_premium"] is True
