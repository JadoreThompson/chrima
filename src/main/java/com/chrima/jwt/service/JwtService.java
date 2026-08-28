package com.chrima.jwt.service;

import com.chrima.jwt.api.IJwtService;
import com.chrima.jwt.config.JwtProperties;
import com.chrima.jwt.exception.JwtException;
import com.chrima.user.api.IUserService;
import com.chrima.user.exception.UserNotFoundException;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletResponse;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;
import java.util.UUID;
import javax.crypto.SecretKey;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class JwtService implements IJwtService {

    private final JwtProperties jwtProperties;
    private final IUserService userService;

    private SecretKey secretKey() {
        byte[] keyBytes = jwtProperties.getSecret().getBytes(StandardCharsets.UTF_8);
        return Keys.hmacShaKeyFor(keyBytes);
    }

    private Instant generateExpiry() {
        return Instant.now().plusSeconds(jwtProperties.getExpirySecs());
    }

    @Override
    public String encode(UUID sub, String email, UUID workspaceId) {
        Instant expiry = generateExpiry();

        var builder = Jwts.builder();

        builder.subject(sub.toString());

        builder.claim("em", email);
        if (workspaceId != null) {
            builder.claim("workspace_id", workspaceId.toString());
        }

        builder.expiration(Date.from(expiry));
        builder.id(UUID.randomUUID().toString());
        builder.issuedAt(Date.from(Instant.now()));
        builder.signWith(secretKey());

        return builder.compact();
    }

    @Override
    public Jwt decode(String token) {
        return decodeInternal(token);
    }

    @Override
    public Jwt decodeJwt(String token) {
        return decodeInternal(token);
    }

    private Jwt decodeInternal(String token) {
        try {
            Claims claims =
                    Jwts.parser().verifyWith(secretKey()).build().parseSignedClaims(token).getPayload();
            String subStr = claims.getSubject();
            String em = claims.get("em", String.class);
            String wsStr = claims.get("workspace_id", String.class);
            Date expDate = claims.getExpiration();
            Date iatDate = claims.getIssuedAt();
            String jti = claims.getId();
            if (subStr == null || em == null || expDate == null) {
                throw new JwtException("Invalid token");
            }
            // validate UUID formats
            UUID.fromString(subStr);
            if (wsStr != null) {
                UUID.fromString(wsStr);
            }
            Instant exp = expDate.toInstant();
            Instant iat = iatDate != null ? iatDate.toInstant() : Instant.now();
            Jwt.Builder builder =
                    Jwt.withTokenValue(token)
                            .header("alg", jwtProperties.getAlgo())
                            .subject(subStr)
                            .issuedAt(iat)
                            .expiresAt(exp);
            builder.claim("em", em);
            if (wsStr != null) {
                builder.claim("workspace_id", wsStr);
            }
            if (jti != null) {
                builder.claim("jti", jti);
            }
            return builder.build();
        } catch (ExpiredJwtException e) {
            throw new JwtException("Token has expired", e);
        } catch (JwtException e) {
            throw e;
        } catch (io.jsonwebtoken.JwtException e) {
            throw new JwtException("Invalid token", e);
        } catch (IllegalArgumentException e) {
            throw new JwtException("Invalid token", e);
        }
    }

    @Override
    public String setCookie(HttpServletResponse response, UUID sub, String email, UUID workspaceId) {
        String token = encode(sub, email, workspaceId);
        Cookie cookie = new Cookie(jwtProperties.getCookieAlias(), token);
        cookie.setHttpOnly(true);
        cookie.setSecure(jwtProperties.isSecure());
        cookie.setPath("/");
        cookie.setMaxAge((int) jwtProperties.getExpirySecs());
        response.addCookie(cookie);
        log.debug("Set JWT cookie alias={} sub={}", jwtProperties.getCookieAlias(), sub);
        return token;
    }

    @Override
    public void removeCookie(HttpServletResponse response) {
        Cookie cookie = new Cookie(jwtProperties.getCookieAlias(), "");
        cookie.setHttpOnly(true);
        cookie.setSecure(jwtProperties.isSecure());
        cookie.setPath("/");
        cookie.setMaxAge(0);
        response.addCookie(cookie);
        log.debug("Removed JWT cookie alias={}", jwtProperties.getCookieAlias());
    }

    @Override
    public Jwt validate(String token) {
        Jwt jwt = decodeJwt(token);
        if (jwt.getExpiresAt() != null && jwt.getExpiresAt().isBefore(Instant.now())) {
            throw new JwtException("Expired jwt token");
        }
        try {
            UUID sub = UUID.fromString(jwt.getSubject());
            String existingToken = userService.getJwtToken(sub);
            if (existingToken == null || !existingToken.equals(token)) {
                throw new JwtException("Invalid jwt token");
            }
        } catch (UserNotFoundException e) {
            throw new JwtException("Invalid jwt token", e);
        }
        return jwt;
    }
}
