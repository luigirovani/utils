from telethon import types as telethon_types
from telethon.types import Message
from telethon.hints import Entity, EntityLike, FullEntity

GroupEntity = telethon_types.Chat | telethon_types.Channel
ChatType = telethon_types.Chat | telethon_types.InputPeerChat | telethon_types.PeerChat
ChannelType = telethon_types.Channel | telethon_types.InputPeerChannel | telethon_types.PeerChannel
UserType = telethon_types.User | telethon_types.InputPeerUser | telethon_types.PeerUser
GroupType = telethon_types.Chat | telethon_types.InputPeerChat | telethon_types.Channel | telethon_types.InputPeerChannel | telethon_types.PeerChat | telethon_types.PeerChannel
BannedGroupType = telethon_types.ChannelForbidden | telethon_types.ChatEmpty | telethon_types.ChatForbidden





