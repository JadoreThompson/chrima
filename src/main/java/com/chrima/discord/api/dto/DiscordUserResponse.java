package com.chrima.discord.api.dto;

import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class DiscordUserResponse {
  String id;
  String username;
  String avatar;
}
