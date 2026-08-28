package com.chrima.user.api.dto;

import java.util.UUID;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class WorkspaceMeta {
  UUID id;
  String name;
}
