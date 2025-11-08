package com.inspect.model;

import lombok.Data;

import javax.persistence.*;
import java.time.LocalDateTime;

/**
 * 设备分组实体
 */
@Entity
@Table(name = "device_group")
@Data
public class DeviceGroup {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(nullable = false)
    private String name;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Column(name = "create_time")
    private LocalDateTime createTime = LocalDateTime.now();
}


