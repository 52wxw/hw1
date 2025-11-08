package com.inspect.service;

import com.inspect.model.Device;
import com.inspect.model.InspectRequest;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

/**
 * 设备巡检编排服务
 */
@Service
public class InspectionService {

    @Value("${services.collect:http://collect-service:8001}")
    private String collectServiceUrl;

    @Value("${services.ai:http://ai-service:8002}")
    private String aiServiceUrl;

    @Autowired
    private DeviceService deviceService;

    @Autowired
    private OperationLogService operationLogService;

    @Autowired
    private RestTemplate restTemplate;

    public Map<String, Object> inspect(Integer userId, Integer deviceId, InspectRequest request) {
        Device device = deviceService.findById(deviceId);
        if (device == null) {
            throw new IllegalArgumentException("设备不存在");
        }

        String password = deviceService.getDecryptedPassword(deviceId);
        if (password == null || password.isEmpty()) {
            throw new IllegalStateException("设备密码缺失");
        }

        Map<String, Object> collectPayload = new HashMap<>();
        collectPayload.put("device_id", deviceId);
        collectPayload.put("ip", device.getIp());
        collectPayload.put("vendor", device.getVendor());
        collectPayload.put("model", device.getModel());
        collectPayload.put("protocol", device.getProtocol());
        collectPayload.put("username", device.getUsername());
        collectPayload.put("password", password);

        Map<String, Object> metrics = invokeCollectService(collectPayload);

        Map<String, Object> analysis = invokeAiService(deviceId, request);

        operationLogService.logOperation(
                userId,
                deviceId,
                "RUN_INSPECTION",
                String.format("巡检设备：%s (%s)", device.getName(), device.getIp()),
                "success"
        );

        Map<String, Object> result = new HashMap<>();
        result.put("metrics", metrics);
        result.put("analysis", analysis);
        return result;
    }

    private Map<String, Object> invokeCollectService(Map<String, Object> payload) {
        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(collectServiceUrl + "/api/collect", payload, Map.class);
            return parseServiceResponse(response, "采集服务调用失败");
        } catch (RestClientException e) {
            throw new IllegalStateException("采集服务不可用：" + e.getMessage(), e);
        }
    }

    private Map<String, Object> invokeAiService(Integer deviceId, InspectRequest request) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("device_id", deviceId);
        payload.put("scenario", request != null && request.getScenario() != null ? request.getScenario() : "手动巡检");
        payload.put("auto_repair", request != null && Boolean.TRUE.equals(request.getAutoRepair()));

        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(aiServiceUrl + "/api/ai/analyze", payload, Map.class);
            return parseServiceResponse(response, "AI 分析服务调用失败");
        } catch (RestClientException e) {
            throw new IllegalStateException("AI 服务不可用：" + e.getMessage(), e);
        }
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> parseServiceResponse(ResponseEntity<Map> response, String defaultMessage) {
        if (!response.getStatusCode().is2xxSuccessful() || response.getBody() == null) {
            throw new IllegalStateException(defaultMessage);
        }

        Object code = response.getBody().get("code");
        if (!(code instanceof Number) || ((Number) code).intValue() != 200) {
            throw new IllegalStateException(defaultMessage + "：" + response.getBody().get("msg"));
        }

        Object dataObj = response.getBody().get("data");
        if (!(dataObj instanceof Map)) {
            throw new IllegalStateException(defaultMessage + "：响应格式错误");
        }
        return (Map<String, Object>) dataObj;
    }
}


