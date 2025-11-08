package com.inspect.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import javax.persistence.*;
import java.time.LocalDateTime;

/**
 * 设备实体类（与数据库表映射）
 * 用Lombok的@Data自动生成getter/setter，解决方法未找到错误
 */
@Entity
@Table(name = "device") // 对应数据库表名
@Data // 关键：自动生成所有字段的getter、setter、toString等
public class Device {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY) // 自增主键
    private Integer id;

    @Column(nullable = false) // 非空约束
    private String name; // 设备名称

    @Column(unique = true, nullable = false) // IP唯一且非空
    private String ip; // 管理IP

    @Column(nullable = false)
    private String vendor; // 厂商（华为/思科）

    @Column(nullable = false)
    private String model; // 设备型号

    private String protocol = "ssh"; // 采集协议，默认ssh

    @Column(nullable = false)
    private String username; // 登录用户名

    @JsonIgnore
    @Column(name = "password_enc", nullable = false) // 对应数据库字段password_enc
    private String passwordEnc; // 加密后的密码（注意字段名：passwordEnc → getPasswordEnc()）

    @Column(name = "group_id")
    private Integer groupId; // 分组ID

    @Transient
    @JsonProperty(access = JsonProperty.Access.WRITE_ONLY)
    private String password; // 明文密码，仅用于创建/更新

    private String status = "offline"; // 状态：online/offline

    private LocalDateTime createTime = LocalDateTime.now(); // 创建时间，默认当前时间
}
