from tortoise import fields
from tortoise.models import Model

from app.constants import NotificationTypes


class Notification(Model):
    """Notification table"""

    id = fields.UUIDField(pk=True)
    user_id = fields.BigIntField()
    channel_id = fields.BigIntField()
    text = fields.CharField(max_length=255)
    notification_type = fields.CharEnumField(enum_type=NotificationTypes)

    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)

    def __str__(self):
        return f"#{self.user_id} - {self.channel_id}"

    class Meta:
        unique_together = ("user_id", "channel_id", "notification_type")
