package com.inspect.model;

import lombok.Data;
import javax.persistence.*;
import java.time.LocalDateTime;

/**
 * 操作日志实体类（审计用）
 */
@Entity
@Table(name = "operation_log")
@Data
public class OperationLog {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "user_id", nullable = false)
    private Integer userId;

    @Column(name = "device_id")
    private Integer deviceId;

    @Column(name = "op_type", nullable = false)
    private String opType; // ADD_DEVICE, UPDATE_DEVICE, DELETE_DEVICE, START_INSPECT, etc.

    @Column(name = "op_content", columnDefinition = "TEXT")
    private String opContent;

    @Column(name = "op_time")
    private LocalDateTime opTime = LocalDateTime.now();

    @Column(nullable = false)
    private String result = "success"; // success/failed
}

