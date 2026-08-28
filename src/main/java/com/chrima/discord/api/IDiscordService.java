package com.chrima.discord.api;

import com.chrima.discord.api.dto.DiscordChannelResponse;
import com.chrima.discord.api.dto.DiscordGuildResponse;
import com.chrima.discord.api.dto.DiscordRoleResponse;
import com.chrima.discord.api.dto.DiscordUserResponse;
import java.util.List;
import java.util.Map;
import java.util.UUID;

public interface IDiscordService {

  Map<String, Object> handleCallback(UUID userId, String code);

  DiscordUserResponse handleSubscriberCallback(String code);

  DiscordUserResponse getMe(UUID userId);

  List<DiscordGuildResponse> getGuilds(UUID userId);

  DiscordGuildResponse getGuild(UUID userId, String guildId);

  List<DiscordChannelResponse> getGuildChannels(UUID userId, String guildId);

  List<DiscordRoleResponse> getGuildRoles(UUID userId, String guildId);
}
