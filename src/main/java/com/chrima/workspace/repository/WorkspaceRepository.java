package com.chrima.workspace.repository;

import com.chrima.workspace.model.Workspace;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface WorkspaceRepository extends JpaRepository<Workspace, UUID> {

  Optional<Workspace> findByExternalId(String externalId);

  List<Workspace> findByUserId(UUID userId);

  Page<Workspace> findByUserId(UUID userId, Pageable pageable);

  Optional<Workspace> findByIdAndUserId(UUID id, UUID userId);
}
