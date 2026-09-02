"""Import all models so SQLAlchemy registers them with Base.metadata"""
from app.models.user import User  # noqa
from app.models.store import Store  # noqa
from app.models.zone import Zone, ZoneSnapshot  # noqa
from app.models.inventory import Inventory, InventoryEvent  # noqa
from app.models.checkout import Checkout  # noqa
from app.models.queue import QueueSnapshot  # noqa
from app.models.staff import Staff  # noqa
from app.models.alert import Alert  # noqa
from app.models.recommendation import Recommendation  # noqa
from app.models.action_result import ActionResult  # noqa
from app.models.event import Event  # noqa
from app.models.sync_event import SyncEvent  # noqa
from app.models.system_health import SystemHealth  # noqa
