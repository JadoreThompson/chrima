package com.chrima.discord.api.dto;

import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class DiscordGuildResponse {
  String id;
  String name;
  String avatar;
}
