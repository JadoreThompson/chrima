package com.chrima.workspace.repository;

import com.chrima.workspace.model.Workspace;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface WorkspaceRepository extends JpaRepository<Workspace, UUID> {

  Optional<Workspace> findByExternalId(String externalId);

  List<Workspace> findByUserId(UUID userId);

  List<Workspace> findByUserId(UUID userId, Pageable pageable);

  @Query(
      value = "SELECT * FROM workspaces WHERE user_id = :userId OFFSET :offset LIMIT :limitPlusOne",
      nativeQuery = true)
  List<Workspace> findByUserIdPaged(
      @Param("userId") UUID userId,
      @Param("offset") int offset,
      @Param("limitPlusOne") int limitPlusOne);

  Optional<Workspace> findByIdAndUserId(UUID id, UUID userId);
}
