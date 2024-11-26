from telethon import types as telethon_types


ChatType = telethon_types.Chat | telethon_types.InputPeerChat
ChannelType = telethon_types.Channel | telethon_types.InputPeerChannel
UserType = telethon_types.User | telethon_types.InputPeerUser
GroupType = telethon_types.Chat | telethon_types.InputPeerChat | telethon_types.Channel | telethon_types.InputPeerChannel




