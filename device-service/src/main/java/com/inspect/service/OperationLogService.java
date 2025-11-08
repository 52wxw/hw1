package com.inspect.service;

import com.inspect.model.OperationLog;
import com.inspect.repository.OperationLogRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.List;

/**
 * 操作日志服务（审计）
 */
@Service
public class OperationLogService {
    @Autowired
    private OperationLogRepository logRepository;

    /**
     * 记录操作日志
     */
    public void logOperation(Integer userId, Integer deviceId, String opType, String opContent, String result) {
        OperationLog log = new OperationLog();
        log.setUserId(userId);
        log.setDeviceId(deviceId);
        log.setOpType(opType);
        log.setOpContent(opContent);
        log.setResult(result);
        logRepository.save(log);
    }

    /**
     * 获取用户操作日志
     */
    public List<OperationLog> getUserLogs(Integer userId) {
        return logRepository.findByUserIdOrderByOpTimeDesc(userId);
    }

    /**
     * 获取设备操作日志
     */
    public List<OperationLog> getDeviceLogs(Integer deviceId) {
        return logRepository.findByDeviceIdOrderByOpTimeDesc(deviceId);
    }
}

