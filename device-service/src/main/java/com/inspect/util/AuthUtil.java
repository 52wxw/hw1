package com.inspect.util;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.MalformedJwtException;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.SignatureException;
import io.jsonwebtoken.UnsupportedJwtException;
import com.inspect.model.User;
import org.mindrot.jbcrypt.BCrypt;
import org.springframework.stereotype.Component;

import java.util.Date;
import java.util.HashMap;
import java.util.Map;

@Component
public class AuthUtil {
    // JWT 密钥（生产环境建议从配置文件读取，如 application.yml）
    private static final String JWT_SECRET = "huawei-ai-inspect-system-2024-secret-key-32bytes-long";
    // Token 过期时间：24小时（86400000 毫秒）
    private static final long JWT_EXPIRATION = 86400000L;

    /**
     * 生成 JWT Token（包含用户ID、用户名、角色）
     */
    public String generateToken(User user) {
        Date now = new Date();
        Date expiryDate = new Date(now.getTime() + JWT_EXPIRATION);

        // Token 负载（自定义字段）
        Map<String, Object> claims = new HashMap<>();
        claims.put("userId", user.getId());
        claims.put("username", user.getUsername());
        claims.put("role", user.getRole());

        // 生成 Token（HS512 算法签名）
        return Jwts.builder()
                .setClaims(claims)
                .setIssuedAt(now)
                .setExpiration(expiryDate)
                .signWith(SignatureAlgorithm.HS512, JWT_SECRET)
                .compact();
    }

    /**
     * 从 Token 中解析用户ID
     */
    public Integer getUserIdFromToken(String token) {
        try {
            Claims claims = Jwts.parser()
                    .setSigningKey(JWT_SECRET)
                    .parseClaimsJws(token)
                    .getBody();
            return Integer.parseInt(claims.get("userId").toString());
        } catch (Exception e) {
            return null;
        }
    }

    /**
     * 验证 Token 有效性（签名、过期、格式）
     */
    public boolean validateToken(String token) {
        try {
            Jwts.parser().setSigningKey(JWT_SECRET).parseClaimsJws(token);
            return true;
        } catch (SignatureException | MalformedJwtException | ExpiredJwtException |
                 UnsupportedJwtException | IllegalArgumentException ex) {
            return false;
        }
    }

    /**
     * bcrypt 密码验证（核心修改：匹配数据库 $2b$ 格式哈希）
     * @param rawPassword 前端输入的明文密码
     * @param storedHash 数据库存储的 bcrypt 哈希值
     * @return 密码是否匹配
     */
    public boolean verifyPassword(String rawPassword, String storedHash) {
        // bcrypt 自带盐值，无需额外处理，直接对比
        return BCrypt.checkpw(rawPassword, storedHash);
    }

    /**
     * bcrypt 密码加密（用于用户注册/修改密码）
     * @param rawPassword 明文密码
     * @return 加密后的 bcrypt 哈希（$2b$ 开头）
     */
    public String hashPassword(String rawPassword) {
        // 盐值强度 12（与 init.sql 中初始化哈希的强度一致）
        return BCrypt.hashpw(rawPassword, BCrypt.gensalt(12));
    }
}
