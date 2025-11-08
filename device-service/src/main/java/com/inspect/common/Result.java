package com.inspect.common;

import lombok.Data;

/**
 * 接口统一返回格式
 * 简化泛型逻辑，避免编译器类型推断失败
 */
@Data
public class Result<T> {
    private int code;       // 响应码：200成功，500失败
    private String msg;     // 响应信息
    private T data;         // 响应数据

    // 成功响应（仅消息）：显式指定泛型为Object，避免推断歧义
    public static Result<Object> success(String msg) {
        Result<Object> result = new Result<>();
        result.setCode(200);
        result.setMsg(msg);
        result.setData(null);
        return result;
    }

    // 成功响应（带数据）：数据类型由入参决定，编译器可直接推断
    public static <T> Result<T> success(T data) {
        Result<T> result = new Result<>();
        result.setCode(200);
        result.setMsg("操作成功");
        result.setData(data);
        return result;
    }

    // 失败响应：显式指定泛型为Object，避免推断歧义
    public static Result<Object> error(String msg) {
        Result<Object> result = new Result<>();
        result.setCode(500);
        result.setMsg(msg);
        result.setData(null);
        return result;
    }

    // （可选）如果需要返回指定泛型的失败响应，可新增重载方法
    public static <T> Result<T> error(String msg, T data) {
        Result<T> result = new Result<>();
        result.setCode(500);
        result.setMsg(msg);
        result.setData(data);
        return result;
    }
}
