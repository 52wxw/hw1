package com.inspect.controller;

import com.inspect.model.User;
import com.inspect.service.AuthService;
import com.inspect.service.OperationLogService;
import com.inspect.util.AuthUtil;
import com.inspect.util.Result;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.servlet.http.HttpServletResponse;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @Autowired
    private AuthService authService;

    @Autowired
    private AuthUtil authUtil;

    @Autowired
    private OperationLogService operationLogService;

    /**
     * 用户登录接口（接收前端用户名/密码，返回 Token 和用户信息）
     */
    @PostMapping("/login")
    public Result<Object> login(@RequestBody Map<String, String> params, HttpServletResponse response) {
        String username = params.get("username");
        String password = params.get("password");

        // 1. 参数校验（非空）
        if (username == null || password == null || username.trim().isEmpty() || password.trim().isEmpty()) {
            return Result.error("用户名和密码不能为空");
        }

        // 2. 调用服务验证用户
        User user = authService.login(username, password);
        if (user == null) {
            // 记录登录失败日志
            operationLogService.logOperation(
                null,
                null,
                "LOGIN",
                String.format("用户 %s 登录失败：用户名或密码错误", username),
                "failed"
            );
            return Result.error("用户名或密码错误");
        }

        // 3. 生成 JWT Token
        String token = authUtil.generateToken(user);

        // 4. 记录登录成功日志
        operationLogService.logOperation(
            user.getId(),
            null,
            "LOGIN",
            String.format("用户 %s 登录成功", username),
            "success"
        );

        // 5. 构建返回数据（Token + 用户信息）
        Map<String, Object> data = new HashMap<>();
        data.put("token", token);
        data.put("user", user);

        return Result.success(data);
    }
}
