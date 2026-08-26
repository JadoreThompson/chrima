package com.chrima.workspace.dto;

import java.util.List;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class PaginatedWorkspaceResponse {
  int page;
  int size;
  boolean hasNext;
  List<WorkspaceResponse> data;
}
