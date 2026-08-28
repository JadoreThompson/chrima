package com.chrima.discord.api.dto;

import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class DiscordChannelResponse {
  String id;
  String name;
}
