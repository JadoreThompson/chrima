package com.chrima.discord.repository;

import com.chrima.discord.model.UserDiscordAccessToken;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserDiscordAccessTokenRepository
    extends JpaRepository<UserDiscordAccessToken, UUID> {}
