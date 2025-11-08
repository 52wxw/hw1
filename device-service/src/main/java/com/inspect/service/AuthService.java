package com.inspect.service;

import com.inspect.model.User;
import com.inspect.repository.UserRepository;
import com.inspect.util.AuthUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class AuthService {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private AuthUtil authUtil;

    /**
     * 用户登录验证（用户名 + 密码）
     * @param username 前端输入用户名
     * @param password 前端输入明文密码
     * @return 验证通过返回 User 对象，失败返回 null
     */
    public User login(String username, String password) {
        // 1. 根据用户名查询数据库（日志已确认用户名能查到）
        User user = userRepository.findByUsername(username);
        if (user == null) {
            return null; // 用户名不存在
        }

        // 2. 核心：用 bcrypt 验证密码（匹配数据库存储的哈希）
        boolean isPasswordValid = authUtil.verifyPassword(password, user.getPasswordHash());
        if (!isPasswordValid) {
            return null; // 密码不匹配
        }

        // 3. 验证通过，返回用户信息（用于生成 Token）
        return user;
    }
}
