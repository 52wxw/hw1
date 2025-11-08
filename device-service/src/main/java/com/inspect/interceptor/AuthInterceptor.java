package com.inspect.interceptor;

import com.inspect.util.AuthUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

@Component
public class AuthInterceptor implements HandlerInterceptor {

    @Autowired
    private AuthUtil authUtil;

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        // 跳过登录接口（无需拦截）
        if (request.getRequestURI().contains("/api/auth/login")) {
            return true;
        }

        // 1. 获取前端传递的 Token（Authorization 头）
        String token = request.getHeader("Authorization");
        if (token == null || token.trim().isEmpty()) {
            response.setStatus(401);
            response.getWriter().write("未授权访问：缺少 Token");
            return false;
        }

        // 2. 解析 Token（处理 Bearer 前缀）
        Integer userId = parseToken(token);
        if (userId == null) {
            response.setStatus(401);
            response.getWriter().write("未授权访问：无效/过期的 Token");
            return false;
        }

        // 3. Token 有效，将用户ID存入请求属性（供后续接口使用）
        request.setAttribute("userId", userId);
        return true;
    }

    /**
     * 解析 Token 获取用户ID（处理 Bearer 前缀 + 验证 Token 有效性）
     */
    private Integer parseToken(String token) {
        try {
            // 移除 Token 中的 "Bearer " 前缀（前端传递格式：Bearer xxxxxx）
            if (token.startsWith("Bearer ")) {
                token = token.substring(7);
            }

            // 验证 Token 有效性 + 解析用户ID
            if (!authUtil.validateToken(token)) {
                return null;
            }
            return authUtil.getUserIdFromToken(token);
        } catch (Exception e) {
            return null;
        }
    }
}
