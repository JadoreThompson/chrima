package com.chrima.discord.api.dto;

import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class DiscordRoleResponse {
  String id;
  String name;
}
