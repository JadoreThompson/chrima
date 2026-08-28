package com.chrima.discord.repository;

import com.chrima.discord.model.DiscordAccessToken;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DiscordAccessTokenRepository extends JpaRepository<DiscordAccessToken, Long> {

  Optional<DiscordAccessToken> findByUserId(long discordUserId);
}
