package com.chrima.tokens.repository;

import com.chrima.tokens.model.Token;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface TokenRepository extends JpaRepository<Token, UUID> {}
